"""Deterministic economics derivation (Step 1.5) — no LLM, pure data grounding.

Stored on the profile: expected_aov_usd, seasonality.
Derived on demand (pure functions of positioning): price_range_for,
target_sensitivity_for — their source maps live in config.py.
"""
from src.derivation import derive_economics, price_range_for, target_sensitivity_for
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


# --- derived-on-demand helpers (not stored) ----------------------------------

def test_price_range_helper_matches_the_bands():
    assert price_range_for("value") == (20.0, 60.0)
    assert price_range_for("premium") == (130.0, 200.0)
    assert price_range_for("luxury") == (200.0, 10_000.0)
    assert price_range_for("unknown") is None


def test_target_sensitivity_helper_maps_from_positioning():
    assert target_sensitivity_for("value") == "high"
    assert target_sensitivity_for("mid") == "medium"
    assert target_sensitivity_for("premium") == "low"
    assert target_sensitivity_for("luxury") == "low"
    assert target_sensitivity_for("unknown") is None
