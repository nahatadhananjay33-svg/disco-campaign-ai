"""Module 4: generate persona-tuned ad creative.

This is the second genuine language task, so it is the LLM's job again. We call
the model once per selected persona (clear and debuggable; easy to show in the
follow-up that each variant is written for one persona). Output is validated by
Pydantic and the prompt forbids unsupported claims.

`llm_call` is injected so tests run offline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from src.config import BANNED_CLAIM_PHRASES
from src.llm import call_json, LLMError
from src.models import AdvertiserProfile, Creative, PersonaMatch

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "creative_generation.md"


def _build_prompt(profile: AdvertiserProfile, persona: dict) -> str:
    template = PROMPT_PATH.read_text()
    return (
        template
        .replace("{profile_json}", profile.model_dump_json(indent=2))
        .replace("{persona_json}", json.dumps(persona, indent=2))
    )


def _advertiser_facts(profile: AdvertiserProfile) -> str:
    """Lowercased blob of everything the advertiser actually stated."""
    parts = [profile.product_category or ""] + profile.subcategories + \
        profile.unique_selling_points + profile.values + profile.brand_tone
    return " ".join(parts).lower()


def _unsupported_text(text: str, facts: str) -> list[str]:
    """Banned claim phrases in `text` that are NOT in the advertiser's own facts."""
    low = text.lower()
    return [p for p in BANNED_CLAIM_PHRASES if p in low and p not in facts]


def _unsupported(creative: Creative, facts: str) -> list[str]:
    """Invented claims across the whole creative (headline + body)."""
    return _unsupported_text(f"{creative.headline} {creative.body}", facts)


def _strip_offending(body: str, facts: str) -> str:
    """Drop any sentence containing an unsupported banned phrase. Returns '' when that
    removes everything, so the caller substitutes a grounded line — never a bare '.'."""
    kept = []
    for sentence in body.replace("!", ".").replace("?", ".").split("."):
        low = sentence.lower()
        if sentence.strip() and not any(p in low and p not in facts for p in BANNED_CLAIM_PHRASES):
            kept.append(sentence.strip())
    return (". ".join(kept) + ".") if kept else ""


def _fallback_creative(profile: AdvertiserProfile, persona: dict) -> Creative:
    """No-LLM fallback: a plain, grounded creative built from the advertiser's own
    USP/values. Not persona-tuned copy, but truthful and functional if the API is down."""
    usp = (profile.unique_selling_points or [profile.product_category or "Our product"])[0]
    vals = ", ".join(profile.values[:2])
    headline = usp[:60].strip().capitalize()
    body = (f"{usp}. {vals}." if vals else f"{usp}.").strip()[:200]
    return Creative(persona_id=persona["id"], persona_name=persona["name"],
                    headline=headline, body=body, messaging_angle="product benefit",
                    reasoning="Template fallback (LLM unavailable); grounded in the advertiser's stated USP/values.")


def generate_creative(
    profile: AdvertiserProfile,
    persona: dict,
    llm_call: Callable[[str], dict] = call_json,
) -> Creative:
    facts = _advertiser_facts(profile)

    def _one() -> Creative:
        raw = llm_call(_build_prompt(profile, persona))
        # The prompt returns copy fields only; we attach the persona identity here
        # so the model can't get the id wrong.
        raw = {**raw, "persona_id": persona["id"], "persona_name": persona["name"]}
        try:
            return Creative.model_validate(raw)
        except ValidationError as exc:
            raise LLMError(f"Creative for {persona['id']} failed validation: {exc}") from exc

    try:
        creative = _one()
    except LLMError:
        return _fallback_creative(profile, persona)   # API down -> template creative
    # Claim guard: regenerate up to twice if the model invented an unsupported claim;
    # as a last resort strip the offending body sentence, and if the HEADLINE itself
    # carries a bad claim, replace it with a grounded one (a real USP/value).
    for _ in range(2):
        if not _unsupported(creative, facts):
            break
        creative = _one()
    if _unsupported(creative, facts):
        # A grounded line pulled from the advertiser's own stated facts, reused for
        # whichever part (body and/or headline) we have to replace.
        grounded = next(
            (s for s in (profile.unique_selling_points + profile.values)
             if s and not _unsupported_text(s, facts)),
            profile.product_category or creative.headline,
        )
        creative.body = _strip_offending(creative.body, facts)
        if not creative.body.strip(" ."):          # stripping removed everything
            creative.body = f"{grounded[:180].strip()}." if grounded else creative.headline
        if _unsupported_text(creative.headline, facts):
            creative.headline = grounded[:60]
    return creative


def generate_creatives(
    profile: AdvertiserProfile,
    selected_personas: list[PersonaMatch],
    personas_by_id: dict[str, dict],
    llm_call: Callable[[str], dict] = call_json,
) -> list[Creative]:
    """One creative per selected persona -> the 3-5 variants the brief asks for."""
    creatives: list[Creative] = []
    for match in selected_personas:
        persona = personas_by_id[match.persona_id]
        creatives.append(generate_creative(profile, persona, llm_call))
    return creatives
