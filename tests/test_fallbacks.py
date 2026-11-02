"""Every LLM-dependent stage degrades gracefully when the API is unavailable."""
import pytest

from src.advertiser_parser import parse_advertiser, _fallback_parse
from src.creative_generator import generate_creative
from src.llm import LLMError
from src.models import AdvertiserProfile, PricePositioning
from src.pipeline import run_pipeline


def _down(_):
    raise LLMError("provider unavailable")


# --- Step 1: parse fallback --------------------------------------------------

def test_fallback_parse_extracts_offline():
    p = _fallback_parse("Luxury apparel — handbags for women, $1200")
    assert p.product_category == "apparel"
    assert p.price_positioning == PricePositioning.luxury
    assert p.price_point_usd == 1200.0
    assert p.target_gender.value == "female"


def test_parse_advertiser_falls_back_when_llm_down():
    p = parse_advertiser("Premium apparel brand, $650", llm_call=_down)
    assert p.product_category == "apparel"
    assert any("fallback mode" in m for m in p.missing_information)


# --- Step 3: creative fallback -----------------------------------------------

def test_generate_creative_falls_back_to_template():
    prof = AdvertiserProfile(product_category="pet", unique_selling_points=["grain-free senior dog food"],
                             values=["vet-formulated"])
    c = generate_creative(prof, {"id": "persona_004", "name": "The Pet Parent"}, llm_call=_down)
    assert c.reasoning.startswith("Template fallback")
    assert "grain-free" in (c.headline + c.body).lower()


# --- Pipeline: matching falls back to the deterministic matcher --------------

def test_pipeline_matching_falls_back_to_deterministic():
    good_profile = {"product_category": "apparel", "subcategories": ["activewear"],
                    "price_positioning": "mid", "confidence": 0.9}
    good_creative = {"headline": "H", "body": "B", "messaging_angle": "a", "reasoning": "r"}
    res = run_pipeline("activewear brand", parse_llm=lambda _: good_profile,
                       match_llm=_down, creative_llm=lambda _: good_creative, matcher="llm")
    assert not res.needs_clarification
    assert res.publishers                                  # matching still produced results
    assert any("deterministic" in n for n in res.degraded_notes)


def test_matching_fallback_is_granular_publisher_fails_persona_survives():
    import re
    good_profile = {"product_category": "apparel", "subcategories": ["activewear"],
                    "price_positioning": "mid", "confidence": 0.9}
    good_creative = {"headline": "H", "body": "B", "messaging_angle": "a", "reasoning": "r"}

    def match_partial(prompt):
        if "avg_order_value" in prompt:                    # the PUBLISHER call -> fail
            raise LLMError("publisher provider down")
        ids = re.findall(r'"id": "(persona_\d+)"', prompt)  # the PERSONA call -> succeed
        return {"matches": [{"id": i, "score": 85 if n < 3 else 20, "reason": "ok"}
                            for n, i in enumerate(ids)]}

    res = run_pipeline("activewear brand", parse_llm=lambda _: good_profile,
                       match_llm=match_partial, creative_llm=lambda _: good_creative, matcher="llm")
    notes = " ".join(res.degraded_notes)
    assert "Publisher matching fell back" in notes          # publisher degraded
    assert "Persona matching fell back" not in notes        # persona kept its LLM result
    assert res.publishers and res.personas
