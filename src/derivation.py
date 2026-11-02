"""Deterministic economics derivation — Step 1.5.

The LLM extracts what the advertiser *said* (category, price, positioning). This
module derives what follows from it, grounded in the catalog's real price scale,
with ZERO LLM involvement — so it is testable, explainable, and cannot drift.

Two kinds of derived value, deliberately handled differently:

  STORED on the profile (independent signals worth precomputing):
    expected_aov_usd  <- stated price if any, else the positioning band midpoint
    seasonality       <- gifting cues in the extracted fields (mirrors pub notes)

  NOT stored — pure functions of price_positioning, exposed as helpers so they
  can never drift from positioning (their source maps live in config.py):
    price_range_for(positioning)        -> POSITIONING_AOV_BAND
    target_sensitivity_for(positioning) -> POSITIONING_TO_TARGET_SENSITIVITY

derive_economics() is called once at the end of parse_advertiser(); matchers and
config read the stored anchors and call the helpers where they need the band/tier.
"""

from __future__ import annotations

from src.config import (
    POSITIONING_AOV_BAND,
    POSITIONING_TO_TARGET_SENSITIVITY,
    SEASONALITY_CUES,
)
from src.models import AdvertiserProfile

# A finite upper bound for "luxury" so a midpoint stays meaningful; above the
# catalog ceiling ($198) we anchor on the band floor rather than a silly average.
_LUXURY_FLOOR = 200.0


# --- Positioning-derived helpers (NOT stored; computed on demand from config) ---

def price_range_for(positioning: str) -> tuple[float, float] | None:
    """(low, high) order-value band for a positioning, or None if unknown."""
    if positioning == "unknown":
        return None
    low, high = POSITIONING_AOV_BAND.get(positioning, POSITIONING_AOV_BAND["unknown"])
    return (float(low), float(high))


def target_sensitivity_for(positioning: str) -> str | None:
    """Persona price_sensitivity tier this positioning should target (low/medium/high)."""
    return POSITIONING_TO_TARGET_SENSITIVITY.get(positioning)


def _expected_aov(positioning: str, price_point: float | None,
                  band: tuple[float, float]) -> float | None:
    """A single price anchor to compare against publisher/persona AOV."""
    if price_point is not None:
        return float(price_point)          # a stated price always wins
    low, high = band
    if positioning == "unknown":
        return None                        # no basis
    if positioning == "luxury":
        return _LUXURY_FLOOR               # above ceiling: anchor on the floor, not a huge midpoint
    return round((low + high) / 2, 1)      # otherwise the middle of the band


def _seasonality(profile: AdvertiserProfile) -> str | None:
    """Scan the extracted fields for gifting/seasonal cues (mirrors pub notes)."""
    blob = " ".join(
        profile.subcategories + profile.values + profile.unique_selling_points
        + profile.target_audience + profile.brand_tone
    ).lower()
    for label, cues in SEASONALITY_CUES.items():
        if any(c in blob for c in cues):
            return label
    return None


def derive_economics(profile: AdvertiserProfile) -> AdvertiserProfile:
    """Populate the STORED derived fields in place and return the profile.
    (price_range / target_sensitivity are not stored — see the helpers above.)"""
    pos = profile.price_positioning.value
    band = POSITIONING_AOV_BAND.get(pos, POSITIONING_AOV_BAND["unknown"])

    profile.expected_aov_usd = _expected_aov(pos, profile.price_point_usd, band)
    profile.seasonality = _seasonality(profile)
    return profile
