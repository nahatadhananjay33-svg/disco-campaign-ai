"""Tests for the deterministic matcher. These are the ones that matter: the
matching logic is our own, so it is the part we must prove is correct and
stable. The LLM parts are validated at their boundary (Pydantic), not here."""

import math

from src.config import PUBLISHER_WEIGHTS
from src.data_loader import load_publishers
from src.models import AdvertiserProfile, PricePositioning
from src.publisher_matcher import rank_publishers


def _premium_dog_food() -> AdvertiserProfile:
    return AdvertiserProfile(
        product_category="pet",
        subcategories=["pet_food", "dog", "senior", "grain-free", "subscription"],
        price_positioning=PricePositioning.premium,
        unique_selling_points=["vet-formulated", "joint health", "longevity"],
        target_audience=["dog owners", "health-conscious"],
        confidence=0.9,
    )


def test_weights_sum_to_one():
    assert math.isclose(sum(PUBLISHER_WEIGHTS.values()), 1.0, abs_tol=1e-9)


def test_pet_publishers_rank_top_for_dog_food():
    ranked = rank_publishers(_premium_dog_food(), load_publishers())
    top3_names = {m.publisher_name for m in ranked[:3]}
    # Pawline and Ruffco are the pet-food publishers; at least one must top the list.
    assert {"Pawline", "Ruffco"} & top3_names
    assert ranked[0].publisher_name in {"Pawline", "Ruffco"}


def test_irrelevant_publishers_are_excluded_with_reason():
    ranked = rank_publishers(_premium_dog_food(), load_publishers())
    excluded = [m for m in ranked if m.excluded]
    assert excluded, "expected some publishers to be excluded for dog food"
    # Every excluded publisher must carry an explanation.
    assert all(m.reason for m in excluded)


def test_scores_are_bounded_and_ordered():
    ranked = rank_publishers(_premium_dog_food(), load_publishers())
    scores = [m.score for m in ranked]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 100.0 for s in scores)


def test_factor_breakdown_present():
    ranked = rank_publishers(_premium_dog_food(), load_publishers())
    top = ranked[0]
    assert {f.name for f in top.factors} == set(PUBLISHER_WEIGHTS)
