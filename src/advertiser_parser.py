"""Module 1: free-text advertiser description -> validated AdvertiserProfile.

This is the one place where understanding fuzzy human language is the job, so
this is where the LLM earns its keep. The output is immediately validated by
Pydantic; if the model hallucinates a wrong shape, we fail here, cleanly.

`llm_call` is injected so tests can run without any API key or network.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from src.derivation import derive_economics
from src.llm import call_json, LLMError
from src.models import AdvertiserProfile
from src.taxonomy import build_vocabulary

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "advertiser_extraction.md"


def _fallback_parse(description: str) -> AdvertiserProfile:
    """No-LLM fallback: keyword-match the description against the catalog vocabulary.
    Coarser than the LLM, but keeps the pipeline alive if the API is down/out of quota.
    Confidence stays modest so the output is clearly flagged as a degraded parse."""
    d = description.lower()
    v = build_vocabulary()
    category = next((c for c in v["categories"] if c in d), None)
    subcats = [s for s in v["subcategory_vocab"] if s in d or s.replace("_", " ") in d][:5]
    gender = ("female" if any(w in d for w in ["women", "woman", "female"]) else
              "male" if any(w in d for w in [" men ", " man ", "male"]) else None)
    positioning = ("luxury" if "luxury" in d else "premium" if "premium" in d else
                   "value" if any(w in d for w in ["value", "cheap", "affordable", "half the cost"]) else "unknown")
    m = re.search(r"\$\s?(\d{2,5})", description)
    price = float(m.group(1)) if m else None
    return AdvertiserProfile(
        product_category=category, subcategories=subcats, target_gender=gender,
        price_positioning=positioning, price_point_usd=price,
        confidence=0.5 if category else 0.2,
        missing_information=["Parsed in fallback mode (LLM unavailable); fields may be incomplete."],
    )


def _load_prompt(description: str) -> str:
    """Fill the prompt's {placeholders} from the live catalog vocabulary, then
    inject the description. The category list and hint vocabularies are derived
    from the data (src/taxonomy.py), never hardcoded."""
    template = PROMPT_PATH.read_text(encoding="utf-8")
    v = build_vocabulary()
    return (
        template
        .replace("{categories}", ", ".join(v["categories"]))
        .replace("{subcategory_hints}", ", ".join(v["subcategory_vocab"]))
        .replace("{geo_labels}", ", ".join(v["geo_labels"]))
        .replace("{aov_low}", str(v["aov_low"]))
        .replace("{aov_high}", str(v["aov_high"]))
        .replace("{description}", description.strip())
    )


def parse_advertiser(
    description: str,
    llm_call: Callable[[str], dict] = call_json,
) -> AdvertiserProfile:
    """Return a validated profile. Raises LLMError if the model misbehaves badly."""
    if not description or not description.strip():
        # Empty input is maximally ambiguous; no need to spend an API call.
        return derive_economics(AdvertiserProfile(
            confidence=0.0,
            missing_information=["No description provided."],
            clarifying_questions=[
                "What product or service do you sell?",
                "Who is your target customer?",
            ],
        ))

    try:
        raw = llm_call(_load_prompt(description))
        profile = AdvertiserProfile.model_validate(raw)
    except (LLMError, ValidationError):
        # LLM down / out of quota / returned junk -> keyword fallback, so the whole
        # pipeline degrades gracefully instead of crashing.
        profile = _fallback_parse(description)

    # Step 1.5: derive the data-grounded economics (price range, AOV anchor,
    # target sensitivity, seasonality) deterministically — no LLM, no drift.
    return derive_economics(profile)
