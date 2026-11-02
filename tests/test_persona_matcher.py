import math

from src.config import MIN_PERSONAS, PERSONA_WEIGHTS, TOP_PERSONAS
from src.data_loader import load_personas
from src.models import AdvertiserProfile, PricePositioning
from src.persona_matcher import match_personas


def _luxury_handbags() -> AdvertiserProfile:
    return AdvertiserProfile(
        product_category="apparel",
        subcategories=["handbags", "leather", "luxury"],
        price_positioning=PricePositioning.luxury,
        unique_selling_points=["Italian-made", "handcrafted"],
        confidence=0.85,
    )


def test_persona_weights_sum_to_one():
    assert math.isclose(sum(PERSONA_WEIGHTS.values()), 1.0, abs_tol=1e-9)


def test_selects_between_min_and_top():
    ranked = match_personas(_luxury_handbags(), load_personas())
    selected = [m for m in ranked if m.selected]
    assert MIN_PERSONAS <= len(selected) <= TOP_PERSONAS


def test_disinterest_demotes_budget_personas_for_luxury():
    # "The Busy Parent" is disinterested in "luxury positioning".
    ranked = match_personas(_luxury_handbags(), load_personas())
    busy = next(m for m in ranked if m.persona_name == "The Busy Parent")
    assert busy.disinterest_conflict is True


def test_scores_bounded_and_sorted():
    ranked = match_personas(_luxury_handbags(), load_personas())
    scores = [m.score for m in ranked]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 100.0 for s in scores)


def test_below_floor_personas_are_never_selected():
    # A skewed ranking (one strong match, the rest sub-floor non-matches, like the
    # LLM returning only one persona) must NOT pad up to MIN_PERSONAS with non-matches.
    from src.config import PERSONA_SELECT_FLOOR
    from src.matching import _select
    from src.models import FactorScore, PersonaMatch

    def mk(name, s):
        return PersonaMatch(persona_id=f"p_{name}", persona_name=name, score=s,
                            factors=[FactorScore(name="llm_fit", raw=s, weight=1.0)],
                            disinterest_conflict=False, reason="")

    got = _select([mk("A", 92), mk("B", 0), mk("C", 0)])
    selected = [m for m in got if m.selected]
    assert [m.persona_name for m in selected] == ["A"]          # only the real match
    assert all(m.score >= PERSONA_SELECT_FLOOR for m in selected)
