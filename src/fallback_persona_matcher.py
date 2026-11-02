"""DETERMINISTIC FALLBACK — persona matcher.

The FALLBACK, not the primary: runs only when the LLM matcher is unavailable, and
in the offline tests. Same philosophy as the fallback publisher matcher —
deterministic, weighted, explainable (weights + their rationale live in config.py,
`PERSONA_WEIGHTS`). One twist: personas carry a `disinterested_in` list, which acts
as a soft veto — if the advertiser hits something the persona actively dislikes, we
don't delete them, we strongly demote them (x0.4) and flag it, so the UI can show why.
"""

from __future__ import annotations

from src.config import (
    MIN_PERSONAS,
    PERSONA_DISINTEREST_MULTIPLIER,
    PERSONA_SELECT_FLOOR,
    PERSONA_WEIGHTS,
    POSITIONING_AOV_BAND,
    TOP_PERSONAS,
)
from src.models import AdvertiserProfile, FactorScore, PersonaMatch
# Reuse the Day 1 tokenizer/coverage helpers instead of re-implementing them.
from src.fallback_publisher_matcher import _coverage, _implied_categories, _tokens

_POSITION_ORDER = ["value", "mid", "mid-premium", "premium", "luxury"]
# Where each price-sensitivity level "wants" to sit on that 0-4 scale.
_SENSITIVITY_IDEAL = {"high": 0.5, "medium": 2.0, "low": 3.5}


def _profile_core(profile: AdvertiserProfile) -> set[str]:
    return _tokens(
        profile.product_category,
        " ".join(profile.subcategories),
        " ".join(profile.unique_selling_points),
    )


def _affinity_factor(profile: AdvertiserProfile, persona: dict) -> float:
    aff = _tokens(" ".join(persona.get("category_affinities", [])))
    core = _profile_core(profile)
    implied = _implied_categories(profile)
    # Best of: advertiser core covered by affinities, or implied category match.
    return max(_coverage(core, aff), _coverage(implied, aff))


def _messaging_factor(profile: AdvertiserProfile, persona: dict) -> float:
    prefs = _tokens(" ".join(persona.get("messaging_preferences", [])))
    msg = _tokens(" ".join(profile.brand_tone), " ".join(profile.unique_selling_points))
    if not msg:
        return 50.0  # no stated tone -> neutral, don't guess
    return _coverage(msg, prefs)


def _price_factor(profile: AdvertiserProfile, persona: dict) -> float:
    pos = profile.price_positioning.value
    if pos == "unknown":
        return 60.0
    ideal = _SENSITIVITY_IDEAL.get(persona.get("price_sensitivity", "medium"), 2.0)
    gap = abs(_POSITION_ORDER.index(pos) - ideal)
    return max(0.0, 100.0 - 25.0 * gap)


def _aov_factor(profile: AdvertiserProfile, persona: dict) -> float:
    low, high = POSITIONING_AOV_BAND[profile.price_positioning.value]
    aov = persona.get("typical_aov_usd")
    if aov is None:
        return 70.0
    if low <= aov <= high:
        return 100.0
    distance = (low - aov) if aov < low else (aov - high)
    return max(0.0, 100.0 - distance)


# A persona's `disinterested_in` is about POSITIONING, not category. These are
# the only tokens we treat as real anti-signals; matching on category nouns like
# "pet" or "food" produces false conflicts (a premium dog food is not a
# "generic pet brand"), so everything else in the phrase is ignored.
_DISINTEREST_QUALIFIERS = {
    "luxury", "premium", "cheap", "budget", "generic", "ultra", "fast",
    "fashion", "novelty", "complicated", "processed", "disposable",
}


def _has_disinterest_conflict(profile: AdvertiserProfile, persona: dict) -> bool:
    disint = _tokens(" ".join(persona.get("disinterested_in", []))) & _DISINTEREST_QUALIFIERS
    if not disint:
        return False
    profile_signals = _profile_core(profile) | _tokens(
        profile.price_positioning.value if profile.price_positioning.value != "unknown" else "",
        " ".join(profile.target_audience),
    )
    return bool(disint & profile_signals)


_FACTOR_FUNCS = {
    "affinity": _affinity_factor,
    "messaging": _messaging_factor,
    "price": _price_factor,
    "aov": _aov_factor,
}


def _reason(persona: dict, factors: list[FactorScore], conflict: bool) -> str:
    ranked = sorted(factors, key=lambda f: f.contribution, reverse=True)
    strengths = [f.name for f in ranked if f.raw >= 70][:2]
    parts = []
    if strengths:
        parts.append(f"Strong {', '.join(strengths)} fit")
    else:
        parts.append("Weak overall fit")
    if conflict:
        parts.append(
            f"demoted: conflicts with this persona's disinterest "
            f"({', '.join(persona.get('disinterested_in', []))})"
        )
    return "; ".join(parts) + "."


def score_persona(profile: AdvertiserProfile, persona: dict) -> PersonaMatch:
    factors = [
        FactorScore(name=n, raw=round(f(profile, persona), 1), weight=PERSONA_WEIGHTS[n])
        for n, f in _FACTOR_FUNCS.items()
    ]
    base = sum(fc.contribution for fc in factors)
    conflict = _has_disinterest_conflict(profile, persona)
    score = round(base * (PERSONA_DISINTEREST_MULTIPLIER if conflict else 1.0), 1)
    return PersonaMatch(
        persona_id=persona["id"],
        persona_name=persona["name"],
        score=score,
        factors=factors,
        disinterest_conflict=conflict,
        reason=_reason(persona, factors, conflict),
    )


def match_personas(profile: AdvertiserProfile, personas: list[dict]) -> list[PersonaMatch]:
    """Score all personas, mark the top 3-5 as `selected` (these drive creatives)."""
    ranked = sorted(
        (score_persona(profile, p) for p in personas),
        key=lambda m: m.score,
        reverse=True,
    )
    # Surface up to MIN_PERSONAS, extending toward TOP_PERSONAS while the next persona
    # is still a respectable match (>= 55% of the top score) — but never select one
    # below PERSONA_SELECT_FLOOR, so a non-match is never shown or given a creative,
    # even if that leaves fewer than MIN_PERSONAS. (Mirrors matching._select.)
    cutoff = ranked[0].score * 0.55 if ranked else 0
    for i, m in enumerate(ranked):
        m.selected = (
            m.score >= PERSONA_SELECT_FLOOR
            and i < TOP_PERSONAS
            and (i < MIN_PERSONAS or m.score >= cutoff)
        )
    return ranked
