"""The orchestrator: one function that runs the whole flow, with a fallback at
every stage so a single failure never takes the whole pipeline down.

description -> profile -> (gate) -> publishers + personas -> (coverage) -> creatives -> config

Fallbacks:
  * parse:    LLM -> keyword extraction (in advertiser_parser)
  * matching: LLM matcher -> deterministic matcher (no API needed)
  * coverage: weak/none -> explain why nothing fits (LLM, with a static fallback)
  * creative: LLM -> template creative (in creative_generator)
  * config:   fully deterministic already
"""

from __future__ import annotations

from typing import Callable

from src.advertiser_parser import parse_advertiser
from src.campaign_builder import build_campaign
from src.config import CONFIDENCE_THRESHOLD
from src.creative_generator import generate_creatives
from src.data_loader import load_personas
from src.llm import call_json, LLMError
from src.matching import coverage_status, explain_gap, get_matcher
from src.models import CampaignResult


def run_pipeline(
    description: str,
    *,
    parse_llm: Callable[[str], dict] = call_json,
    match_llm: Callable[[str], dict] = call_json,
    creative_llm: Callable[[str], dict] = call_json,
    matcher: str = "llm",
) -> CampaignResult:
    personas = load_personas()
    personas_by_id = {p["id"]: p for p in personas}
    degraded: list[str] = []

    profile = parse_advertiser(description, llm_call=parse_llm)
    if any("fallback mode" in m for m in profile.missing_information):
        degraded.append("Advertiser parsing ran in keyword-fallback mode (LLM unavailable).")

    # Confidence gate: don't invent a campaign from "idk just try it".
    if profile.is_ambiguous(CONFIDENCE_THRESHOLD):
        return CampaignResult(profile=profile, needs_clarification=True, degraded_notes=degraded)

    # Matching — publisher and persona each fall back to the deterministic matcher
    # INDEPENDENTLY, so a failure on one doesn't lose the other's LLM result. Each
    # branch always returns the proper Pydantic list (PublisherMatch / PersonaMatch).
    kwargs = {"llm_call": match_llm} if matcher == "llm" else {}
    primary = get_matcher(matcher, **kwargs)
    deterministic = get_matcher("deterministic")

    def _rank(method: str, kind: str):
        try:
            return getattr(primary, method)(profile)
        except LLMError:
            degraded.append(f"{kind} matching fell back to the deterministic matcher (LLM unavailable).")
            return getattr(deterministic, method)(profile)

    ranked_publishers = _rank("rank_publishers", "Publisher")
    ranked_personas = _rank("rank_personas", "Persona")
    selected = [mm for mm in ranked_personas if mm.selected]

    # Coverage: be honest when the catalog doesn't really fit.
    coverage = coverage_status(ranked_publishers)
    coverage_note = ""
    if coverage in ("weak", "none"):
        try:
            coverage_note = explain_gap(profile, "publisher", match_llm)
        except LLMError:
            coverage_note = "No strong match in the current catalog (LLM explanation unavailable)."

    # Off-catalog: don't fabricate a campaign/creatives for a doomed match.
    if coverage == "none":
        return CampaignResult(
            profile=profile, coverage=coverage, coverage_note=coverage_note,
            degraded_notes=degraded, publishers=ranked_publishers, personas=ranked_personas,
        )

    creatives = generate_creatives(profile, selected, personas_by_id, llm_call=creative_llm)
    if any(c.reasoning.startswith("Template fallback") for c in creatives):
        degraded.append("Some creatives used the template fallback (LLM unavailable).")
    campaign = build_campaign(profile, ranked_publishers, selected, personas_by_id, creatives=creatives)

    return CampaignResult(
        profile=profile, needs_clarification=False, coverage=coverage, coverage_note=coverage_note,
        degraded_notes=degraded, publishers=ranked_publishers, personas=ranked_personas,
        creatives=creatives, campaign=campaign,
    )
