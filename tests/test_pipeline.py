"""End-to-end wiring test with stubbed LLMs — proves the whole pipeline runs
without any API key."""

from src.config import PERSONA_SELECT_FLOOR, TOP_PERSONAS
from src.pipeline import run_pipeline
from tests.conftest import creative_stub, make_parse_stub


def test_full_pipeline_happy_path(dog_food_profile):
    result = run_pipeline(
        "premium senior dog food",
        parse_llm=make_parse_stub(dog_food_profile),
        creative_llm=creative_stub,
        matcher="deterministic",
    )
    assert result.needs_clarification is False
    assert result.publishers and result.publishers[0].publisher_name in {"Pawline", "Ruffco"}
    assert 1 <= len(result.creatives) <= TOP_PERSONAS
    # one creative per selected persona, and we never select a non-match
    selected = [m for m in result.personas if m.selected]
    assert len(result.creatives) == len(selected)
    assert all(m.score >= PERSONA_SELECT_FLOOR for m in selected)
    assert result.campaign is not None
    assert sum(a.budget_percentage for a in result.campaign.publishers) == 100


def test_vague_input_asks_for_clarification(vague_profile):
    result = run_pipeline(
        "we help people feel better",
        parse_llm=make_parse_stub(vague_profile),
        creative_llm=creative_stub,
        matcher="deterministic",
    )
    assert result.needs_clarification is True
    assert result.profile.clarifying_questions
    assert result.creatives == []       # no invented campaign
    assert result.campaign is None
