"""Campaign economics: AOV anchor (stated price -> publisher-mean -> persona),
category-based CVR with a high-ticket exception, and the derived CPA/CPC/budget."""
from src.campaign_builder import _effective_aov, _category_cvr, build_campaign
from src.models import AdvertiserProfile, PersonaMatch, PublisherMatch, FactorScore, PricePositioning

PBYID = {"p_affluent": {"typical_aov_usd": 145, "price_sensitivity": "low"},
         "p_pet": {"typical_aov_usd": 72, "price_sensitivity": "low-medium"},
         "p_busy": {"typical_aov_usd": 78, "price_sensitivity": "medium"}}
PUBS = {"pub_a": {"avg_order_value_usd": 73}, "pub_b": {"avg_order_value_usd": 63}}


def _pm(pid):
    return PersonaMatch(persona_id=pid, persona_name=pid, score=80, factors=[], reason="", selected=True)


def _pub(pid):
    return PublisherMatch(publisher_id=pid, publisher_name=pid, score=80,
                          factors=[FactorScore(name="x", raw=80, weight=1.0)], reason="")


def test_stated_price_wins():
    hb = AdvertiserProfile(price_positioning=PricePositioning.luxury, price_point_usd=1200)
    aov, src = _effective_aov(hb, [], [], PBYID, {})
    assert aov == 1200.0 and "stated" in src


def test_no_price_uses_publisher_mean_aov():
    df = AdvertiserProfile(product_category="pet", price_positioning=PricePositioning.premium)
    aov, src = _effective_aov(df, [_pub("pub_a"), _pub("pub_b")], [], PBYID, PUBS)
    assert aov == 68.0 and "publishers" in src          # mean(73, 63)


def test_no_price_no_publishers_falls_back_to_personas():
    df = AdvertiserProfile(product_category="pet", price_positioning=PricePositioning.premium)
    aov, src = _effective_aov(df, [], [_pm("p_pet"), _pm("p_busy")], PBYID, {})
    assert aov == 75.0 and "personas" in src            # mean(72, 78)


def test_cvr_is_category_based_not_positioning():
    # premium DOG FOOD must convert like pet (2.5%), NOT like luxury.
    df = AdvertiserProfile(product_category="pet", price_positioning=PricePositioning.premium)
    cvr, _ = _category_cvr(df, aov=60)
    assert cvr == 0.025


def test_high_ticket_item_drops_to_luxury_cvr():
    bag = AdvertiserProfile(product_category="apparel", price_positioning=PricePositioning.luxury)
    cvr, basis = _category_cvr(bag, aov=1200)           # apparel base 2.8% but high-ticket
    assert cvr == 0.012 and "high-ticket" in basis


def test_economics_end_to_end_for_luxury_handbag():
    prof = AdvertiserProfile(product_category="apparel", subcategories=["handbags"],
                             price_positioning=PricePositioning.luxury, price_point_usd=1200)
    cfg = build_campaign(prof, [_pub("pub_a")], [_pm("p_affluent")], PBYID)
    assert cfg.bid_strategy.target_cpa_usd == 360.0                 # 0.30 * 1200
    assert cfg.forecast.estimated_cvr == 0.012                     # high-ticket
    lo, hi = cfg.bid_strategy.suggested_cpc_range_usd              # around 360*0.012 = 4.32
    assert lo < 4.32 < hi
    assert cfg.budget.daily_budget == 5400.0                       # 15 * 360
    assert cfg.budget.total_budget == 5400.0 * 30                  # flight
    assert cfg.forecast.expected_roas == round(1200 / 360, 1)
