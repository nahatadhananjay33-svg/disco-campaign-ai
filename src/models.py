"""Pydantic models = the typed contracts between modules.

Every boundary where the LLM hands data to deterministic code goes through one
of these. If the LLM returns junk, validation fails here instead of blowing up
three modules later. That is the whole reason we use Pydantic.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class PricePositioning(str, Enum):
    value = "value"
    mid = "mid"
    mid_premium = "mid-premium"
    premium = "premium"
    luxury = "luxury"
    unknown = "unknown"


class TargetGender(str, Enum):
    female = "female"
    male = "male"
    all = "all"


class BusinessModel(str, Enum):
    dtc = "dtc"
    subscription = "subscription"
    b2b = "b2b"
    marketplace = "marketplace"
    other = "other"


class AdvertiserProfile(BaseModel):
    """Structured representation of a free-text advertiser description.

    Every field is the advertiser-side mirror of a field we match against in
    publishers.json / shopper_personas.json, so matching has something concrete
    to compare. The LLM fills ONLY what the prompt states or strongly implies;
    anything not stated stays null/empty (no hallucination). Produced in
    src/advertiser_parser.py, consumed by the deterministic matchers.
    """

    # --- A. Product & category (core matching signal) ---
    product_category: str | None = Field(
        None, description="Broad category → publisher.category / persona.category_affinities."
    )
    subcategories: list[str] = Field(
        default_factory=list, description="Finer product tags → publisher.subcategories."
    )

    # --- B. Audience (who they sell to) ---
    target_gender: TargetGender | None = Field(
        None, description="→ publisher.audience.gender_split / persona.gender_skew."
    )
    target_age_range: str | None = Field(
        None, description="e.g. '25-40' → publisher.audience.age_skew / persona.age_range."
    )
    target_audience: list[str] = Field(
        default_factory=list, description="Free descriptors, e.g. 'dog owners', 'eco-conscious'."
    )
    target_geography: list[str] = Field(
        default_factory=list, description="→ publisher.audience.top_geos."
    )

    # --- C. Price & economics ---
    price_positioning: PricePositioning = Field(
        PricePositioning.unknown,
        description="→ publisher.audience.income_tier / persona.price_sensitivity.",
    )
    price_point_usd: float | None = Field(
        None, description="A stated price (e.g. 650, 1200) → avg_order_value_usd / typical_aov_usd."
    )

    # --- C2. Derived economics (filled DETERMINISTICALLY after extraction by
    #         src/derivation.py — NOT by the LLM). The positioning $-band itself
    #         is not stored (it would duplicate price_positioning and could drift);
    #         it lives in config.POSITIONING_AOV_BAND and is read on demand. ---
    expected_aov_usd: float | None = Field(
        None, description="Single price anchor: the stated price if given, else the positioning band midpoint."
    )
    seasonality: str | None = Field(
        None, description="Gifting/seasonal signal mirrored from publisher notes, e.g. 'gifting'."
    )

    # --- D. Brand & messaging (for creative + persona fit) ---
    brand_tone: list[str] = Field(
        default_factory=list, description="→ persona.messaging_preferences."
    )
    values: list[str] = Field(
        default_factory=list,
        description="Ethos (sustainable, handmade, vegan…) → persona.disinterested_in / affinities.",
    )
    unique_selling_points: list[str] = Field(
        default_factory=list, description="→ publisher.notes + grounds the creative."
    )

    # --- E. Business meta ---
    business_model: BusinessModel | None = Field(
        None, description="Drives campaign objective + off-catalog (b2b) detection."
    )
    brand_name: str | None = Field(None, description="Attribution metadata.")

    # --- F. Interpretation quality (not matched — drives the gate) ---
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="How sure the model is it understood the input."
    )
    missing_information: list[str] = Field(default_factory=list)
    clarifying_questions: list[str] = Field(default_factory=list)

    def is_ambiguous(self, threshold: float = 0.45) -> bool:
        """Below this, we ask questions instead of inventing a campaign."""
        return self.confidence < threshold


class FactorScore(BaseModel):
    """One line of the scoring breakdown, so the UI can show *why* a score happened."""

    name: str
    raw: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0)

    @property
    def contribution(self) -> float:
        return self.raw * self.weight


class PublisherMatch(BaseModel):
    publisher_id: str
    publisher_name: str
    score: float = Field(..., ge=0.0, le=100.0)
    factors: list[FactorScore]
    reason: str
    excluded: bool = False


class PersonaMatch(BaseModel):
    persona_id: str
    persona_name: str
    score: float = Field(..., ge=0.0, le=100.0)
    factors: list[FactorScore]
    disinterest_conflict: bool = False
    reason: str
    selected: bool = False


class Creative(BaseModel):
    """One ad variant, tuned for a single persona. Produced by the LLM."""

    persona_id: str
    persona_name: str
    headline: str
    body: str
    messaging_angle: str
    reasoning: str = Field(..., description="Why this copy fits the persona.")


# --- Campaign config (our chosen shape; justified in the README) ---

class PublisherAllocation(BaseModel):
    publisher_id: str
    publisher_name: str
    budget_percentage: int = Field(..., ge=0, le=100)


class Targeting(BaseModel):
    personas: list[str]                 # who to speak to (matched shopper segments)
    interests: list[str]                # interest keywords for audience targeting
    geographies: list[str]              # where to serve (from publisher geos / advertiser)
    age_range: str | None = None        # demographic narrowing (from the advertiser)
    gender: str | None = None


class Budget(BaseModel):
    currency: str = "USD"
    daily_budget: float                 # sized to buy the target conversions/day
    total_budget: float | None = None   # daily x flight length (lifetime cap)
    flight_days: int | None = None      # campaign length assumption
    pacing: str = "even"                # spend the daily budget evenly through the day
    basis: str = "assumption"           # the brief gives no budget; this is suggested


class BidStrategy(BaseModel):
    type: str                           # e.g. "target_cpa", "max_clicks"
    target_cpa_usd: float | None = None
    suggested_cpc_range_usd: tuple[float, float] | None = None
    aggressiveness: str | None = None   # conservative / balanced / aggressive (from price-sensitivity)
    rationale: str


class Forecast(BaseModel):
    """Estimated outcomes — what the budget/bids are expected to buy. Makes the
    config read like a real ad plan, and every number is auditable from its basis."""
    estimated_cvr: float                # category benchmark (+ high-ticket adjustment)
    cvr_basis: str                      # the source/assumption behind the CVR
    target_conversions_per_day: int
    estimated_clicks_per_day: int
    estimated_impressions_per_day: int
    available_monthly_impressions: int  # inventory pool across recommended publishers
    expected_roas: float                # revenue per ad dollar at target CPA


class KpiTargets(BaseModel):
    target_cpa_usd: float               # the CPA the campaign is judged against
    target_roas: float                  # the ROAS the campaign is judged against


class Measurement(BaseModel):
    """How success is defined and measured — without this, CVR/CPA can't be computed."""
    conversion_event: str               # what counts as a conversion (purchase / lead)
    attribution_window_days: int        # how long after a click a conversion still counts
    optimization_goal: str              # what the system optimizes for
    kpi_targets: KpiTargets


class PredictedVsActual(BaseModel):
    cvr: float | None = None
    cpa_usd: float | None = None
    conversions_per_day: float | None = None
    roas: float | None = None


class Feedback(BaseModel):
    """Predicted vs actual. `actual` is null until the campaign runs; once filled, the
    gap between predicted and actual is the TRAINING LABEL for a learned ranker — this
    is how the system bootstraps from zero-shot LLM to a data-driven model."""
    predicted: PredictedVsActual
    actual: PredictedVsActual
    note: str


class CampaignConfig(BaseModel):
    campaign_id: str                    # unique id to join logged results back to this config
    created_at: str                     # when the plan was generated
    status: str = "draft"               # needs human approval before launch
    objective: str
    advertiser_category: str | None
    targeting: Targeting
    publishers: list[PublisherAllocation]
    budget: Budget
    bid_strategy: BidStrategy
    forecast: Forecast | None = None
    measurement: Measurement | None = None
    feedback: Feedback | None = None
    assumptions: list[str] = Field(default_factory=list)


class CampaignResult(BaseModel):
    """Everything the UI needs for one run."""

    profile: AdvertiserProfile
    needs_clarification: bool = False
    coverage: str = "good"          # good | weak | none — how well the catalog fits
    coverage_note: str = ""         # on weak/none: why nothing fits + what would
    degraded_notes: list[str] = Field(default_factory=list)  # any LLM-fallback that kicked in
    publishers: list[PublisherMatch] = Field(default_factory=list)
    personas: list[PersonaMatch] = Field(default_factory=list)
    creatives: list[Creative] = Field(default_factory=list)
    campaign: CampaignConfig | None = None
