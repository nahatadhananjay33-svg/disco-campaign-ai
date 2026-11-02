from src.campaign_builder import build_campaign
from src.data_loader import load_personas, load_publishers
from src.models import AdvertiserProfile, PricePositioning
from src.fallback_persona_matcher import match_personas
from src.fallback_publisher_matcher import rank_publishers


def _profile() -> AdvertiserProfile:
    return AdvertiserProfile(
        product_category="pet",
        subcategories=["pet_food", "dog", "senior"],
        price_positioning=PricePositioning.premium,
        unique_selling_points=["vet-formulated"],
        business_model="subscription",
        confidence=0.9,
    )


def _build():
    profile = _profile()
    pubs = rank_publishers(profile, load_publishers())
    personas_by_id = {p["id"]: p for p in load_personas()}
    selected = [m for m in match_personas(profile, load_personas()) if m.selected]
    return build_campaign(profile, pubs, selected, personas_by_id)


def test_budget_sums_to_100():
    cfg = _build()
    assert sum(a.budget_percentage for a in cfg.publishers) == 100


def test_recommended_publishers_are_not_excluded():
    profile = _profile()
    pubs = rank_publishers(profile, load_publishers())
    cfg = _build()
    rec_ids = {a.publisher_id for a in cfg.publishers}
    excluded_ids = {m.publisher_id for m in pubs if m.excluded}
    assert not (rec_ids & excluded_ids)


def test_assumptions_are_labeled():
    cfg = _build()
    # Budget and CPA must be flagged as assumptions, never silent facts.
    assert any("budget" in a.lower() for a in cfg.assumptions)
    assert any("cpa" in a.lower() for a in cfg.assumptions)
    assert cfg.budget.basis == "assumption"


def test_b2b_objective_is_lead_gen():
    profile = _profile()
    profile.business_model = "b2b"
    pubs = rank_publishers(profile, load_publishers())
    personas_by_id = {p["id"]: p for p in load_personas()}
    selected = [m for m in match_personas(profile, load_personas()) if m.selected]
    cfg = build_campaign(profile, pubs, selected, personas_by_id)
    assert cfg.objective == "lead_generation"
