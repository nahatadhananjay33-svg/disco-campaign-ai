"""Generalization tests over a 35-case synthetic dataset (data/synthetic_advertisers.json).

These test the DETERMINISTIC engine (publisher/persona matching + campaign
builder) against hand-authored "golden" profiles that stand in for what the LLM
would extract. They prove the engine stays valid and sensible far beyond the 15
seed examples — any category wins the right publishers, off-catalog inputs are
flagged as weak coverage, and the campaign config is always internally valid.

The LLM's *actual* parsing of the raw text is exercised live through the app
(`streamlit run app.py`); these offline tests cover the deterministic engine.
"""

import json
from pathlib import Path

import pytest

from src.config import PERSONA_SELECT_FLOOR, TOP_PERSONAS
from src.models import AdvertiserProfile
from src.pipeline import run_pipeline

DATASET = json.loads(
    (Path(__file__).resolve().parent.parent / "data" / "synthetic_advertisers.json").read_text()
)


def _stub(profile_dict):
    return lambda prompt: profile_dict


def _creative_stub(prompt):
    return {
        "headline": "Made for you",
        "body": "Built around what you care about.",
        "messaging_angle": "fit",
        "reasoning": "matches the persona",
    }


def _run(case):
    return run_pipeline(
        case["text"], parse_llm=_stub(case["profile"]), creative_llm=_creative_stub, matcher="deterministic"
    )


ids = [c["id"] for c in DATASET]


@pytest.mark.parametrize("case", DATASET, ids=ids)
def test_profile_validates(case):
    # Every golden profile must be a valid AdvertiserProfile.
    AdvertiserProfile.model_validate(case["profile"])


@pytest.mark.parametrize("case", [c for c in DATASET if c["kind"] != "ambiguous"],
                         ids=[c["id"] for c in DATASET if c["kind"] != "ambiguous"])
def test_non_ambiguous_produces_valid_campaign(case):
    r = _run(case)
    assert r.needs_clarification is False
    # Off-catalog with no coverage: we honestly return no campaign, not a forced one.
    if r.coverage == "none":
        assert r.campaign is None and r.creatives == []
        assert r.publishers and all(m.excluded for m in r.publishers)
        return
    # publisher invariants
    assert len(r.publishers) == 20
    scores = [m.score for m in r.publishers]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= s <= 100 for s in scores)
    assert all(m.reason for m in r.publishers if m.excluded)
    # persona invariants: at least one real match, never a padded non-match
    selected = [m for m in r.personas if m.selected]
    assert 1 <= len(selected) <= TOP_PERSONAS
    assert all(m.score >= PERSONA_SELECT_FLOOR for m in selected)
    # campaign invariants
    assert r.campaign is not None
    assert sum(a.budget_percentage for a in r.campaign.publishers) == 100
    assert r.campaign.assumptions
    # one creative per selected persona
    assert len(r.creatives) == len(selected)


@pytest.mark.parametrize("case", [c for c in DATASET if c["kind"] == "clear"],
                         ids=[c["id"] for c in DATASET if c["kind"] == "clear"])
def test_clear_cases_rank_right_category_on_top(case):
    r = _run(case)
    top_non_excluded = next(m for m in r.publishers if not m.excluded)
    from src.data_loader import load_publishers
    cat = {p["id"]: p["category"] for p in load_publishers()}[top_non_excluded.publisher_id]
    assert cat in case["expect_top_categories"], (
        f"{case['id']}: top publisher category {cat!r} not in {case['expect_top_categories']}"
    )


@pytest.mark.parametrize("case", [c for c in DATASET if c["kind"] == "off_catalog"],
                         ids=[c["id"] for c in DATASET if c["kind"] == "off_catalog"])
def test_off_catalog_flags_weak_coverage(case):
    r = _run(case)
    # Off-catalog must be flagged as weak/none coverage — never a confident campaign.
    assert r.coverage in ("weak", "none"), f"{case['id']}: expected weak/none, got {r.coverage}"
    if r.coverage == "none":
        assert r.campaign is None
    else:  # weak: best-available campaign, flagged in its assumptions
        assert any("coverage" in a.lower() for a in r.campaign.assumptions)


@pytest.mark.parametrize("case", [c for c in DATASET if c["kind"] == "ambiguous"],
                         ids=[c["id"] for c in DATASET if c["kind"] == "ambiguous"])
def test_ambiguous_cases_are_gated(case):
    r = _run(case)
    assert r.needs_clarification is True
    assert r.creatives == []
    assert r.campaign is None
