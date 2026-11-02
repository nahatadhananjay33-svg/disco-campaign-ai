"""Deterministic economics derivation (Step 1.5) — no LLM, pure data grounding.

Stored on the profile: expected_aov_usd, seasonality.
"""
from src.derivation import derive_economics
from src.models import AdvertiserProfile, PricePositioning


def _p(**kw):
    return AdvertiserProfile(**kw)


# --- stored fields -----------------------------------------------------------

def test_luxury_with_stated_price_uses_the_price_and_flags_gifting():
    p = derive_economics(_p(product_category="apparel",
                            subcategories=["handbags", "gifting"],
                            price_positioning=PricePositioning.luxury,
                            price_point_usd=1200))
    assert p.expected_aov_usd == 1200.0             # stated price wins
    assert p.seasonality == "gifting"               # from the 'gifting' subcat


def test_value_no_price_uses_band_midpoint():
    p = derive_economics(_p(product_category="wellness_dtc",
                            price_positioning=PricePositioning.value))
    assert p.expected_aov_usd == 40.0               # midpoint of the value band
    assert p.seasonality is None


def test_premium_no_price_anchors_on_band_midpoint():
    p = derive_economics(_p(price_positioning=PricePositioning.premium))
    assert p.expected_aov_usd == 165.0


def test_luxury_without_price_anchors_on_the_floor_not_a_huge_midpoint():
    p = derive_economics(_p(price_positioning=PricePositioning.luxury))
    assert p.expected_aov_usd == 200.0              # floor, not (200+10000)/2


def test_unknown_positioning_carries_no_anchor():
    p = derive_economics(_p(price_positioning=PricePositioning.unknown))
    assert p.expected_aov_usd is None
