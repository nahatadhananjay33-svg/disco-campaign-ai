"""DETERMINISTIC FALLBACK matchers — publisher + persona, in one place.

These are the FALLBACK, not the primary. They run only when the LLM matcher
(src/matching.py, the shipped primary) is unavailable, and in the offline test suite.
Deliberately NOT an LLM: predictable, inspectable, testable — the same profile always
produces the same ranking, and every number is explainable. Plain weighted Python;
each factor returns 0-100, combined with the weights in config.py (`PUBLISHER_WEIGHTS`
/ `PERSONA_WEIGHTS` — see there for WHY those weights), and we keep the per-factor
breakdown so the UI can show the work.

The two scorers live together because they share the tokenizer/coverage helpers below.

One persona twist: personas carry a `disinterested_in` list, a soft veto — if the
advertiser hits something the persona dislikes, we don't delete them, we demote them
(x0.4) and flag it.
"""

from __future__ import annotations

import re

from src.config import (
    MIN_PERSONAS,
    PERSONA_DISINTEREST_MULTIPLIER,
    PERSONA_SELECT_FLOOR,
    PERSONA_WEIGHTS,
    POSITIONING_AOV_BAND,
    PUBLISHER_EXCLUSION_THRESHOLD,
    PUBLISHER_WEIGHTS,
    TOP_PERSONAS,
)
from src.models import AdvertiserProfile, FactorScore, PersonaMatch, PublisherMatch


# ============================================================================
# Shared helpers (used by both the publisher and persona scorers)
# ============================================================================

_STOPWORDS = {"and", "the", "for", "with", "our", "we", "a", "of", "to", "is", "that"}

# Maps advertiser-side words to the publisher categories they imply. Keeps
# "dog food" matching the "pet" category even though the words differ.
_CATEGORY_SYNONYMS = {
    "pet": "pet", "dog": "pet", "cat": "pet", "puppy": "pet", "kitten": "pet",
    "apparel": "apparel", "clothing": "apparel", "activewear": "apparel",
    "outerwear": "apparel", "shoes": "apparel", "handbag": "apparel",
    "handbags": "apparel", "leather": "apparel", "socks": "apparel",
    "bedding": "home", "linen": "home", "bath": "home", "home": "home",
    "cookware": "home", "kitchen": "home", "candle": "home", "candles": "home",
    "beverage": "beverages", "beverages": "beverages", "drink": "beverages",
    "soda": "beverages", "sparkling": "beverages",
    "supplement": "wellness_dtc", "supplements": "wellness_dtc",
    "vitamins": "wellness_dtc", "protein": "wellness_dtc", "creatine": "wellness_dtc",
    "beauty": "beauty", "skincare": "beauty", "makeup": "beauty", "haircare": "beauty",
    "grocery": "groceries", "groceries": "groceries", "organic": "groceries",
    "pantry": "groceries",
    "meal": "meal_kits", "mealkit": "meal_kits",
    "wellness": "wellness_services", "fitness": "wellness_services",
    "yoga": "wellness_services", "spa": "wellness_services",
}


def _tokens(*parts: object) -> set[str]:
    """Normalize any text (and underscores) into a set of meaningful tokens."""
    text = " ".join(str(p) for p in parts if p).lower()
    raw = re.split(r"[^a-z0-9]+", text)
    return {t for t in raw if t and t not in _STOPWORDS and len(t) > 1}


def _profile_tokens(profile: AdvertiserProfile) -> set[str]:
    return _tokens(
        profile.product_category,
        " ".join(profile.subcategories),
        " ".join(profile.unique_selling_points),
        " ".join(profile.target_audience),
    )


def _implied_categories(profile: AdvertiserProfile) -> set[str]:
    """Which publisher categories does this advertiser point to?"""
    cats: set[str] = set()
    for tok in _tokens(profile.product_category, " ".join(profile.subcategories)):
        if tok in _CATEGORY_SYNONYMS:
            cats.add(_CATEGORY_SYNONYMS[tok])
    if profile.product_category:
        cats.add(profile.product_category.lower().strip())
    return cats


def _coverage(a: set[str], b: set[str]) -> float:
    """Fraction of `a` found in `b`, 0-100. Asymmetric on purpose: we care how
    much of the *advertiser* is covered by the publisher/persona."""
    if not a:
        return 0.0
    return 100.0 * len(a & b) / len(a)


# ============================================================================
# Publisher scorer  (weights: PUBLISHER_WEIGHTS)
# ============================================================================

def _pub_category_factor(profile: AdvertiserProfile, pub: dict) -> float:
    implied = _implied_categories(profile)
    pub_cat = pub["category"].lower()
    pub_sub_tokens = _tokens(" ".join(pub.get("subcategories", [])))
    if pub_cat in implied:
        return 100.0
    # partial credit if the advertiser's category words show up in subcategories
    if implied & pub_sub_tokens:
        return 70.0
    return 0.0


def _pub_subcategory_factor(profile: AdvertiserProfile, pub: dict) -> float:
    prof = _profile_tokens(profile)
    pub_tokens = _tokens(
        pub["category"], " ".join(pub.get("subcategories", [])), pub.get("notes", "")
    )
    return _coverage(prof, pub_tokens)


def _pub_audience_factor(profile: AdvertiserProfile, pub: dict) -> float:
    """Gender is the only audience signal this dataset really supports.

    Key design choice: a missing/unmeasurable audience is NEUTRAL (60), not a
    zero. Absence of evidence is not evidence of a mismatch, so we only drop
    below neutral when the advertiser's stated gender *conflicts* with the
    publisher's dominant audience.
    """
    aud_tokens = _tokens(" ".join(profile.target_audience))
    gender = pub["audience"].get("gender_split", {})
    dominant = max(gender, key=gender.get) if gender and max(gender.values()) >= 0.6 else None

    wants_female = bool({"women", "woman", "female", "moms", "mom", "she"} & aud_tokens)
    wants_male = bool({"men", "man", "male"} & aud_tokens)

    if dominant == "female" and wants_female:
        return 90.0
    if dominant == "male" and wants_male:
        return 90.0
    if dominant == "female" and wants_male:
        return 30.0  # real conflict: targeting men on an 80%+ female publisher
    if dominant == "male" and wants_female:
        return 30.0
    return 60.0  # no measurable signal either way -> neutral, don't punish category fit


def _pub_aov_factor(profile: AdvertiserProfile, pub: dict) -> float:
    low, high = POSITIONING_AOV_BAND[profile.price_positioning.value]
    aov = pub["avg_order_value_usd"]
    if low <= aov <= high:
        return 100.0
    # decay linearly with distance outside the band
    distance = (low - aov) if aov < low else (aov - high)
    return max(0.0, 100.0 - distance)  # ~$1 AOV gap == 1 point


def _pub_positioning_factor(profile: AdvertiserProfile, pub: dict) -> float:
    if profile.price_positioning.value == "unknown":
        return 70.0  # neutral-ish when we don't know
    # Infer the publisher's positioning from its AOV, then measure ordinal gap.
    order = ["value", "mid", "mid-premium", "premium", "luxury"]
    aov = pub["avg_order_value_usd"]
    pub_pos = (
        "value" if aov < 40 else "mid" if aov < 75 else
        "mid-premium" if aov < 120 else "premium" if aov < 200 else "luxury"
    )
    gap = abs(order.index(pub_pos) - order.index(profile.price_positioning.value))
    return max(0.0, 100.0 - 30.0 * gap)


_PUBLISHER_FACTORS = {
    "category": _pub_category_factor,
    "subcategory": _pub_subcategory_factor,
    "audience": _pub_audience_factor,
    "aov": _pub_aov_factor,
    "positioning": _pub_positioning_factor,
}


def _publisher_reason(pub: dict, factors: list[FactorScore], excluded: bool) -> str:
    ranked = sorted(factors, key=lambda f: f.contribution, reverse=True)
    strengths = [f.name for f in ranked if f.raw >= 70][:2]
    drags = [f.name for f in ranked if f.raw < 40]
    if excluded:
        weak = drags or [ranked[-1].name]
        return f"Excluded: weak {', '.join(weak)} fit ({pub['category']} publisher)."
    parts = []
    if strengths:
        parts.append(f"Strong {', '.join(strengths)} match")
    if drags:
        parts.append(f"but limited {', '.join(drags)}")
    note = pub.get("notes", "").rstrip(".")
    return ". ".join(p for p in [", ".join(parts), note] if p) + "."


def score_publisher(profile: AdvertiserProfile, pub: dict) -> PublisherMatch:
    factors = [
        FactorScore(name=name, raw=round(func(profile, pub), 1), weight=PUBLISHER_WEIGHTS[name])
        for name, func in _PUBLISHER_FACTORS.items()
    ]
    total = round(sum(f.contribution for f in factors), 1)
    excluded = total <= PUBLISHER_EXCLUSION_THRESHOLD
    return PublisherMatch(
        publisher_id=pub["id"],
        publisher_name=pub["name"],
        score=total,
        factors=factors,
        reason=_publisher_reason(pub, factors, excluded),
        excluded=excluded,
    )


def rank_publishers(profile: AdvertiserProfile, publishers: list[dict]) -> list[PublisherMatch]:
    """Score every publisher and return them sorted best-first."""
    matches = [score_publisher(profile, pub) for pub in publishers]
    return sorted(matches, key=lambda m: m.score, reverse=True)


# ============================================================================
# Persona scorer  (weights: PERSONA_WEIGHTS)
# ============================================================================

_POSITION_ORDER = ["value", "mid", "mid-premium", "premium", "luxury"]
# Where each price-sensitivity level "wants" to sit on that 0-4 scale.
_SENSITIVITY_IDEAL = {"high": 0.5, "medium": 2.0, "low": 3.5}


def _profile_core(profile: AdvertiserProfile) -> set[str]:
    return _tokens(
        profile.product_category,
        " ".join(profile.subcategories),
        " ".join(profile.unique_selling_points),
    )


def _per_affinity_factor(profile: AdvertiserProfile, persona: dict) -> float:
    aff = _tokens(" ".join(persona.get("category_affinities", [])))
    core = _profile_core(profile)
    implied = _implied_categories(profile)
    # Best of: advertiser core covered by affinities, or implied category match.
    return max(_coverage(core, aff), _coverage(implied, aff))


def _per_messaging_factor(profile: AdvertiserProfile, persona: dict) -> float:
    prefs = _tokens(" ".join(persona.get("messaging_preferences", [])))
    msg = _tokens(" ".join(profile.brand_tone), " ".join(profile.unique_selling_points))
    if not msg:
        return 50.0  # no stated tone -> neutral, don't guess
    return _coverage(msg, prefs)


def _per_price_factor(profile: AdvertiserProfile, persona: dict) -> float:
    pos = profile.price_positioning.value
    if pos == "unknown":
        return 60.0
    ideal = _SENSITIVITY_IDEAL.get(persona.get("price_sensitivity", "medium"), 2.0)
    gap = abs(_POSITION_ORDER.index(pos) - ideal)
    return max(0.0, 100.0 - 25.0 * gap)


def _per_aov_factor(profile: AdvertiserProfile, persona: dict) -> float:
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


_PERSONA_FACTORS = {
    "affinity": _per_affinity_factor,
    "messaging": _per_messaging_factor,
    "price": _per_price_factor,
    "aov": _per_aov_factor,
}


def _persona_reason(persona: dict, factors: list[FactorScore], conflict: bool) -> str:
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
        for n, f in _PERSONA_FACTORS.items()
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
        reason=_persona_reason(persona, factors, conflict),
    )


def match_personas(profile: AdvertiserProfile, personas: list[dict]) -> list[PersonaMatch]:
    """Score all personas, mark the strongest (up to 5) as `selected` (these drive creatives)."""
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
