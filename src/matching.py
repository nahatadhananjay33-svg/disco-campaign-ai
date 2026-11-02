"""Module 2+3: match an advertiser to publishers and shopper personas.

Two strategies behind one `Matcher` interface so they're interchangeable:
  * LLMMatcher (SHIPPED): a Groq LLM scores every publisher/persona 0-100 with a
    reason, reading the real fields (category, AOV, income, gender, affinities,
    disinterest, …). Matching is a judgement about audience fit, which is exactly
    what an LLM does better than a keyword/weight system.
  * DeterministicMatcher (FALLBACK): structured rules + lexical overlap, no API
    (src/publisher_matcher.py + src/persona_matcher.py). Used automatically by the
    pipeline when the LLM is unavailable, and by the offline tests.

Both return the same Pydantic objects (PublisherMatch / PersonaMatch), so callers
never care which one ran. `llm_call` is injectable so everything tests offline.

Also here: `coverage_status()` (is the catalog a good/weak/no fit?) and
`explain_gap()` (on weak/none, the LLM explains why nothing fits + what would).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

import src.persona_matcher as pem
import src.publisher_matcher as pm
from src.config import (
    GOOD_MATCH_THRESHOLD,
    MIN_PERSONAS,
    PERSONA_SELECT_FLOOR,
    PUBLISHER_EXCLUSION_THRESHOLD,
    TOP_PERSONAS,
)
from src.data_loader import load_personas, load_publishers
from src.llm import call_json
from src.models import AdvertiserProfile, FactorScore, PersonaMatch, PublisherMatch

_PROMPTS = Path(__file__).resolve().parent.parent / "prompts"

# LLM post-filter: a publisher is only "recommended" if it clears the bar AND is
# not far below the top pick — stops the model clustering everything at 60-90.
LLM_RECOMMEND_GAP = 25.0


# --- compact views fed to the LLM ------------------------------------------
# We send the LLM only the fields that mirror each target's schema (a publisher is
# an audience we buy — demographics + economics; a persona is a shopper — affinity
# + messaging + price). Fewer, relevant fields = sharper judgement, less noise.

def _pub_brief(pub: dict) -> dict:
    """Every publisher meta field the LLM should weigh (incl. monthly_impressions
    as the reach/scale signal)."""
    a = pub.get("audience", {})
    return {"id": pub["id"], "name": pub["name"], "category": pub["category"],
            "subcategories": pub.get("subcategories", []),
            "avg_order_value_usd": pub.get("avg_order_value_usd"),
            "monthly_impressions": pub.get("monthly_impressions"),
            "audience": {"age": a.get("age_skew"), "gender_split": a.get("gender_split"),
                         "income_tier": a.get("income_tier"), "geos": a.get("top_geos")},
            "notes": pub.get("notes", "")}


def _per_brief(p: dict) -> dict:
    """Every persona meta field: demographics, affinities, price signals, the
    disinterest veto, the messaging angles, and the behavioural description."""
    return {"id": p["id"], "name": p["name"], "affinities": p.get("category_affinities", []),
            "age_range": p.get("age_range"), "gender_skew": p.get("gender_skew"),
            "price_sensitivity": p.get("price_sensitivity"), "typical_aov_usd": p.get("typical_aov_usd"),
            "messaging_preferences": p.get("messaging_preferences", []),
            "disinterested_in": p.get("disinterested_in", []), "description": p.get("description", "")}


def _profile_brief(profile: AdvertiserProfile) -> dict:
    """The advertiser profile minus the internal gate fields."""
    return profile.model_dump(exclude={"confidence", "missing_information", "clarifying_questions"})


# The advertiser-side fields fed alongside each target (mirror of its schema).
PUB_PROFILE_FIELDS = {"product_category", "subcategories", "target_gender", "target_age_range",
                      "target_audience", "target_geography", "price_positioning", "price_point_usd",
                      "expected_aov_usd", "seasonality"}
PER_PROFILE_FIELDS = {"product_category", "subcategories", "target_gender", "target_age_range",
                      "target_audience", "price_positioning", "price_point_usd", "expected_aov_usd",
                      "seasonality", "brand_tone", "values", "unique_selling_points"}


def _profile_brief_for(profile: AdvertiserProfile, fields: set) -> dict:
    return {k: v for k, v in profile.model_dump().items() if k in fields}


def _llm_scores(prompt_file: str, profile_brief: dict, items_key: str,
                items: list[dict], llm_call: Callable[[str], dict]) -> dict[str, dict]:
    """Fill the prompt, call the LLM, parse {id: {score, reason}}. Retries up to 3x
    on an empty/malformed reply (a transient JSON glitch); a hard provider failure
    raises LLMError straight through, so the pipeline can fall back deterministically."""
    template = (_PROMPTS / prompt_file).read_text(encoding="utf-8")
    prompt = (template
              .replace("{profile_json}", json.dumps(profile_brief, default=str))
              .replace(f"{{{items_key}}}", json.dumps(items)))

    def _parse(r):  # models sometimes return a bare list instead of {"matches": [...]}
        o: dict[str, dict] = {}
        for m in (r if isinstance(r, list) else (r or {}).get("matches", [])):
            if "id" in m:
                o[m["id"]] = {"score": float(m.get("score", 0)), "reason": m.get("reason", "")}
        return o

    out: dict[str, dict] = {}
    for _ in range(3):
        out = _parse(llm_call(prompt))
        if out:
            break
    return out


def _select(matches: list[PersonaMatch]) -> list[PersonaMatch]:
    """Mark the personas we recommend: the strongest few that clear PERSONA_SELECT_FLOOR.
    We surface up to MIN_PERSONAS plus any others in the top TOP_PERSONAS within 55% of
    the best score — but a persona below the floor is a non-match (often one the LLM
    never scored), so it is never selected, never shown, and never given a creative,
    even if that leaves fewer than MIN_PERSONAS."""
    cutoff = matches[0].score * 0.55 if matches else 0
    for i, m in enumerate(matches):
        m.selected = (
            m.score >= PERSONA_SELECT_FLOOR
            and i < TOP_PERSONAS
            and (i < MIN_PERSONAS or m.score >= cutoff)
        )
    return matches


# --- interface + the two strategies ----------------------------------------

class Matcher(ABC):
    """Common interface: both methods return the same Pydantic lists."""
    name = "base"

    @abstractmethod
    def rank_publishers(self, profile: AdvertiserProfile) -> list[PublisherMatch]: ...

    @abstractmethod
    def rank_personas(self, profile: AdvertiserProfile) -> list[PersonaMatch]: ...


class DeterministicMatcher(Matcher):
    """No-API fallback: structured rules + lexical overlap (src/*_matcher.py)."""
    name = "deterministic"

    def rank_publishers(self, profile):
        return pm.rank_publishers(profile, load_publishers())

    def rank_personas(self, profile):
        return pem.match_personas(profile, load_personas())


class LLMMatcher(Matcher):
    """Shipped: a Groq LLM scores each publisher/persona fit + reason, one call each."""
    name = "llm"

    def __init__(self, llm_call: Callable[[str], dict] = call_json):
        self.llm_call = llm_call

    def rank_publishers(self, profile):
        pubs = load_publishers()
        sc = _llm_scores("publisher_match.md", _profile_brief_for(profile, PUB_PROFILE_FIELDS),
                         "publishers_json", [_pub_brief(p) for p in pubs], self.llm_call)
        scores = {p["id"]: round(min(100.0, max(0.0, sc.get(p["id"], {}).get("score", 0.0))), 1) for p in pubs}
        top = max(scores.values(), default=0.0)
        out = []
        for p in pubs:
            s = scores[p["id"]]
            # Recommended only if it clears the bar AND isn't far below the best pick.
            excluded = (s <= PUBLISHER_EXCLUSION_THRESHOLD) or (s < top - LLM_RECOMMEND_GAP)
            out.append(PublisherMatch(publisher_id=p["id"], publisher_name=p["name"], score=s,
                                      factors=[FactorScore(name="llm_fit", raw=s, weight=1.0)],
                                      reason=sc.get(p["id"], {}).get("reason", ""), excluded=excluded))
        return sorted(out, key=lambda m: m.score, reverse=True)

    def rank_personas(self, profile):
        pers = load_personas()
        sc = _llm_scores("persona_match.md", _profile_brief_for(profile, PER_PROFILE_FIELDS),
                         "personas_json", [_per_brief(p) for p in pers], self.llm_call)
        out = []
        for p in pers:
            s = round(min(100.0, max(0.0, sc.get(p["id"], {}).get("score", 0.0))), 1)
            out.append(PersonaMatch(persona_id=p["id"], persona_name=p["name"], score=s,
                                    factors=[FactorScore(name="llm_fit", raw=s, weight=1.0)],
                                    disinterest_conflict=False, reason=sc.get(p["id"], {}).get("reason", "")))
        return _select(sorted(out, key=lambda m: m.score, reverse=True))


# --- coverage fallback (honest "no match") ---------------------------------

def coverage_status(matches: list) -> str:
    """'good' | 'weak' | 'none' — how well the catalog covers this advertiser."""
    rec = [m for m in matches if not m.excluded]
    if not rec:
        return "none"
    return "good" if rec[0].score >= GOOD_MATCH_THRESHOLD else "weak"


def explain_gap(profile: AdvertiserProfile, kind: str, llm_call: Callable[[str], dict] = call_json) -> str:
    """Weak/no coverage -> the LLM explains why nothing fits and what WOULD. Falls
    back to a static note if the LLM is also unavailable."""
    prompt = (f"No strong {kind} match was found in our catalog for this advertiser:\n"
              f"{json.dumps(_profile_brief(profile), default=str)}\n\n"
              f"In 1-2 sentences, explain why our catalog doesn't cover them well and describe "
              f'the ideal {kind} that WOULD fit (even if not in our catalog). Return ONLY JSON: {{"note": "..."}}')
    try:
        return llm_call(prompt).get("note", "")
    except Exception:
        return f"No strong {kind} fit in the current catalog; shown best-available (low confidence)."


MATCHERS = {m.name: m for m in [DeterministicMatcher, LLMMatcher]}


def get_matcher(name: str, **kwargs) -> Matcher:
    cls = MATCHERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown matcher {name!r}. Options: {list(MATCHERS)}")
    return cls() if name == "deterministic" else cls(**kwargs)
