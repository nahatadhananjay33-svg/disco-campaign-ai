"""Shared test fixtures / LLM stubs so the whole pipeline runs offline."""

import pytest


def make_parse_stub(profile_dict: dict):
    """Return a fake parse LLM that always yields `profile_dict`."""
    return lambda prompt: profile_dict


def creative_stub(prompt: str) -> dict:
    """A fake creative LLM: returns a valid, generic creative regardless of input."""
    return {
        "headline": "Thoughtful nutrition for your dog",
        "body": "Vet-formulated, grain-free food for senior dogs, delivered on your schedule.",
        "messaging_angle": "health and convenience",
        "reasoning": "Matches the persona's stated preferences.",
    }


@pytest.fixture
def dog_food_profile() -> dict:
    return {
        "brand_name": None,
        "product_category": "pet",
        "subcategories": ["pet_food", "dog", "senior", "grain-free", "subscription"],
        "price_positioning": "premium",
        "unique_selling_points": ["vet-formulated", "joint health", "longevity"],
        "target_audience": ["dog owners", "health-conscious"],
        "brand_tone": ["caring", "science-backed"],
        "business_model": "subscription",
        "confidence": 0.9,
        "missing_information": [],
        "clarifying_questions": [],
    }


@pytest.fixture
def vague_profile() -> dict:
    return {
        "brand_name": None,
        "product_category": None,
        "subcategories": [],
        "price_positioning": "unknown",
        "unique_selling_points": [],
        "target_audience": [],
        "brand_tone": [],
        "business_model": None,
        "confidence": 0.1,
        "missing_information": ["product", "audience"],
        "clarifying_questions": ["What do you sell?", "Who is it for?"],
    }
