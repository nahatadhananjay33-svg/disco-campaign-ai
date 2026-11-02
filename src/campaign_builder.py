"""Module 5: assemble the structured campaign config.

Deterministic — a human needs to trust and edit this, so it must be predictable.
Everything the brief didn't give us (budget, CPA, CVR, flight) is DERIVED from the
product economics and surfaced as a clearly-labeled `assumption`, never a silent
fact. The economic chain (all justified in the README / fields doc):

  AOV  = stated price, else the recommended publishers' average order value
  CPA  = 30% of AOV                         (pay ~1/3 of order value to acquire)
  CVR  = category benchmark, dropped to the luxury rate only for high-ticket items
  CPC  = CPA x CVR                          (a click is worth its conversion chance)
  budget/day = target_conversions/day x CPA (scales with the product's economics)
"""

from __future__ import annotations

import statistics
import uuid
from datetime import datetime, timezone

from src.config import (
    ATTRIBUTION_WINDOW_DAYS,
    CVR_BY_CATEGORY,
    CVR_SOURCE,
    DEFAULT_CTR,
    DEFAULT_CVR,
    DEFAULT_DAILY_BUDGET_USD,
    DEFAULT_FLIGHT_DAYS,
    DEFAULT_GEOS,
    DEFAULT_TARGET_CPA_USD,
    HIGH_TICKET_THRESHOLD_USD,
    LUXURY_CVR,
    TARGET_CONVERSIONS_PER_DAY,
    TARGET_CPA_FRACTION_OF_AOV,
    TOP_PUBLISHERS,
)
from src.data_loader import load_publishers
from src.models import (
    AdvertiserProfile,
    Budget,
    BidStrategy,
    CampaignConfig,
    CreativeRef,
    Feedback,
    Forecast,
    KpiTargets,
    Measurement,
    PersonaMatch,
    PredictedVsActual,
    PublisherAllocation,
    PublisherMatch,
    Targeting,
)

_SENSITIVITY_SCORE = {"low": 1.0, "low-medium": 0.5, "medium": 0.0,
                      "medium-high": -0.5, "high": -1.0}


def _pubs_by_id() -> dict[str, dict]:
    return {p["id"]: p for p in load_publishers()}


def _allocate_budget(matches: list[PublisherMatch]) -> list[PublisherAllocation]:
    """Split 100% across publishers in proportion to match score; fix rounding."""
    total = sum(m.score for m in matches) or 1.0
    allocs = [
        PublisherAllocation(publisher_id=m.publisher_id, publisher_name=m.publisher_name,
                            budget_percentage=round(100 * m.score / total))
        for m in matches
    ]
    drift = 100 - sum(a.budget_percentage for a in allocs)
    if allocs and drift:
        allocs[0].budget_percentage += drift
    return allocs


def _effective_aov(
    profile: AdvertiserProfile,
    recommended: list[PublisherMatch],
    selected_personas: list[PersonaMatch],
    personas_by_id: dict[str, dict],
    pubs: dict[str, dict],
) -> tuple[float | None, str]:
    """Order value to anchor CPA/budget on, in priority order:
      1. the advertiser's STATED price (a real number for THIS product);
      2. else the RECOMMENDED publishers' average AOV (the target audience's basket);
      3. else the selected personas' typical AOV.
    Never the positioning-band midpoint — that overstates everyday products."""
    if profile.price_point_usd:
        return float(profile.price_point_usd), "the advertiser's stated product price"
    pub = [pubs[m.publisher_id].get("avg_order_value_usd") for m in recommended if m.publisher_id in pubs]
    pub = [a for a in pub if a]
    if pub:
        return round(statistics.mean(pub), 2), "the recommended publishers' average order value (no price stated)"
    pa = [personas_by_id[m.persona_id].get("typical_aov_usd") for m in selected_personas]
    pa = [a for a in pa if a]
    if pa:
        return round(statistics.mean(pa), 2), "the selected personas' typical order value"
    return None, "no basis to estimate order value"


def _category_cvr(profile: AdvertiserProfile, aov: float | None) -> tuple[float, str]:
    """Conversion rate from CATEGORY (grounded in benchmarks), dropped to the luxury
    rate only when the item is genuinely high-ticket — not from a 'premium' label."""
    cat = profile.product_category or ""
    base = CVR_BY_CATEGORY.get(cat, DEFAULT_CVR)
    if aov and aov >= HIGH_TICKET_THRESHOLD_USD:
        cvr = min(base, LUXURY_CVR)
        return cvr, (f"{cvr*100:.1f}% — high-ticket item (${aov:.0f} >= ${HIGH_TICKET_THRESHOLD_USD:.0f}), "
                     f"converts at the luxury rate. {CVR_SOURCE}")
    return base, f"{base*100:.1f}% — '{cat or 'unknown'}' category benchmark. {CVR_SOURCE}"


def _interests(profile: AdvertiserProfile) -> list[str]:
    seen, out = set(), []
    for item in profile.subcategories + profile.unique_selling_points:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out[:6]


def _geographies(pub_ids: list[str], pubs: dict[str, dict]) -> list[str]:
    geos: list[str] = []
    for pid in pub_ids:
        for g in pubs.get(pid, {}).get("audience", {}).get("top_geos", []):
            if g not in geos:
                geos.append(g)
    return geos or DEFAULT_GEOS


def _bid_aggressiveness(selected: list[PersonaMatch], personas_by_id: dict[str, dict]) -> str:
    """Price-sensitive audiences need tighter bids; low-sensitivity buyers convert
    even at higher bids, so we can bid up."""
    scores = [_SENSITIVITY_SCORE.get(personas_by_id[m.persona_id].get("price_sensitivity", "medium"), 0.0)
              for m in selected if m.persona_id in personas_by_id]
    avg = statistics.mean(scores) if scores else 0.0
    return "aggressive" if avg > 0.3 else "conservative" if avg < -0.3 else "balanced"


def build_campaign(
    profile: AdvertiserProfile,
    ranked_publishers: list[PublisherMatch],
    selected_personas: list[PersonaMatch],
    personas_by_id: dict[str, dict],
    creatives: list | None = None,
) -> CampaignConfig:
    assumptions: list[str] = []
    pubs = _pubs_by_id()

    recommended = [m for m in ranked_publishers if not m.excluded][:TOP_PUBLISHERS]
    if not recommended:
        recommended = ranked_publishers[:3]
        assumptions.append("The catalog has weak coverage for this advertiser; publishers "
                           "shown are best-available and low-confidence.")

    allocations = _allocate_budget(recommended)
    objective = "lead_generation" if (profile.business_model or "").lower() == "b2b" else "conversions"

    # --- economics ---
    aov, aov_source = _effective_aov(profile, recommended, selected_personas, personas_by_id, pubs)
    cvr, cvr_basis = _category_cvr(profile, aov)

    if aov:
        target_cpa = round(aov * TARGET_CPA_FRACTION_OF_AOV, 2)
        cpc = round(target_cpa * cvr, 2)
        daily_budget = round(TARGET_CONVERSIONS_PER_DAY * target_cpa, 2)
        assumptions.append(f"Target CPA ${target_cpa:.0f} = {int(TARGET_CPA_FRACTION_OF_AOV*100)}% of "
                           f"{aov_source} (${aov:.0f}); implied ROAS ~{1/TARGET_CPA_FRACTION_OF_AOV:.1f}x.")
        assumptions.append(f"Assumed conversion rate {cvr_basis}")
        assumptions.append(f"Suggested CPC ${cpc:.2f} = CPA x CVR (${target_cpa:.0f} x {cvr*100:.1f}%).")
        assumptions.append(f"Daily budget ${daily_budget:.0f} = {TARGET_CONVERSIONS_PER_DAY} target "
                           f"conversions/day x ${target_cpa:.0f} CPA. Cap to audience reach in production.")
    else:
        target_cpa, cpc, daily_budget = DEFAULT_TARGET_CPA_USD, round(DEFAULT_TARGET_CPA_USD * cvr, 2), DEFAULT_DAILY_BUDGET_USD
        assumptions.append(f"No price or audience AOV to anchor on; using default CPA ${target_cpa:.0f} "
                           f"and ${daily_budget:.0f}/day.")

    total_budget = round(daily_budget * DEFAULT_FLIGHT_DAYS, 2)
    assumptions.append(f"Flight assumed {DEFAULT_FLIGHT_DAYS} days -> total budget ${total_budget:.0f}.")

    # --- forecast (what the spend buys) ---
    clicks = round(daily_budget / cpc) if cpc else 0
    impressions = round(clicks / DEFAULT_CTR) if DEFAULT_CTR else 0
    reach_pool = sum(pubs[m.publisher_id].get("monthly_impressions", 0) for m in recommended if m.publisher_id in pubs)
    forecast = Forecast(
        estimated_cvr=round(cvr, 4), cvr_basis=cvr_basis,
        target_conversions_per_day=TARGET_CONVERSIONS_PER_DAY if aov else 0,
        estimated_clicks_per_day=clicks, estimated_impressions_per_day=impressions,
        available_monthly_impressions=reach_pool,
        expected_roas=round(aov / target_cpa, 1) if aov else round(1 / TARGET_CPA_FRACTION_OF_AOV, 1),
    )
    assumptions.append(f"Assumed display CTR {DEFAULT_CTR*100:.1f}% to estimate {impressions:,} "
                       f"impressions/day; {reach_pool:,} monthly impressions available across recommended publishers.")

    aggressiveness = _bid_aggressiveness(selected_personas, personas_by_id)
    bid = BidStrategy(
        type="target_cpa", target_cpa_usd=float(target_cpa),
        suggested_cpc_range_usd=(round(cpc * 0.8, 2), round(cpc * 1.2, 2)),
        aggressiveness=aggressiveness,
        rationale=(f"{objective} objective, target-CPA strategy. CPA anchored to {aov_source} "
                   f"(${aov:.0f}); CPC = CPA x {cvr*100:.1f}% CVR; {aggressiveness} bidding from the "
                   f"audience's price-sensitivity." if aov else
                   f"{objective} objective on defaults (no AOV basis)."),
    )

    creative_refs = [CreativeRef(persona_id=c.persona_id, persona_name=c.persona_name, headline=c.headline)
                     for c in (creatives or [])]

    # --- measurement: how success is defined (needed to even compute CVR/CPA) ---
    conversion_event = "lead" if objective == "lead_generation" else "purchase"
    measurement = Measurement(
        conversion_event=conversion_event,
        attribution_window_days=ATTRIBUTION_WINDOW_DAYS,
        optimization_goal="minimize_cpa",
        kpi_targets=KpiTargets(target_cpa_usd=float(target_cpa),
                               target_roas=round(aov / target_cpa, 1) if aov else round(1 / TARGET_CPA_FRACTION_OF_AOV, 1)),
    )
    assumptions.append(f"Success = a '{conversion_event}' within {ATTRIBUTION_WINDOW_DAYS} days of a click; "
                       "optimize to minimize CPA against the KPI targets.")

    # --- feedback: predicted now; `actual` filled post-launch -> training labels ---
    feedback = Feedback(
        predicted=PredictedVsActual(cvr=round(cvr, 4), cpa_usd=float(target_cpa),
                                    conversions_per_day=float(TARGET_CONVERSIONS_PER_DAY if aov else 0),
                                    roas=forecast.expected_roas),
        actual=PredictedVsActual(),  # null until the campaign runs
        note=("Fill `actual` after launch; the predicted-vs-actual gap (per publisher/persona) is the "
              "training label that moves this system from zero-shot LLM to a learned ranker."),
    )

    return CampaignConfig(
        campaign_id=f"camp_{profile.product_category or 'x'}_{uuid.uuid4().hex[:8]}",
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        status="draft",
        objective=objective,
        advertiser_category=profile.product_category,
        targeting=Targeting(
            personas=[m.persona_id for m in selected_personas],
            interests=_interests(profile),
            geographies=_geographies([a.publisher_id for a in allocations], pubs),
            age_range=profile.target_age_range,
            gender=profile.target_gender.value if profile.target_gender else None,
        ),
        publishers=allocations,
        budget=Budget(daily_budget=float(daily_budget), total_budget=total_budget, flight_days=DEFAULT_FLIGHT_DAYS),
        bid_strategy=bid,
        forecast=forecast,
        measurement=measurement,
        feedback=feedback,
        creatives=creative_refs,
        assumptions=assumptions,
    )
