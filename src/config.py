"""All tunable knobs live here, on purpose.

In the interview they may ask us to "change the weighting" live. Because every
weight is one place, that is a one-line edit — not a hunt through the matcher.
These are *design choices*, not learned parameters. In production we would tune
them against real campaign outcomes (see README).
"""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# --- Publisher scoring weights (must sum to 1.0) ---
PUBLISHER_WEIGHTS = {
    "category": 0.40,      # does the advertiser's category match the publisher's?
    "subcategory": 0.25,   # finer keyword overlap (pet_food, sustainable, ...)
    "audience": 0.15,      # does the target audience line up?
    "aov": 0.10,           # is the publisher's spend level compatible?
    "positioning": 0.10,   # premium vs value alignment
}

# A publisher scoring at or below this is shown as "excluded", with a reason.
PUBLISHER_EXCLUSION_THRESHOLD = 35.0

# Fallback (Tier 2): if the best non-excluded match is below this, we treat the
# catalog as having weak coverage for this advertiser and say so, rather than
# presenting a weak match as a confident one.
GOOD_MATCH_THRESHOLD = 50.0

# How many publishers / personas we surface by default.
TOP_PUBLISHERS = 5
TOP_PERSONAS = 5
MIN_PERSONAS = 3

# A persona scoring below this is a non-match (often one the LLM didn't even
# return, which defaults to 0). We neither display it nor spend a creative call
# on it — a couple of real personas beat three padded with non-matches. We still
# surface MIN_PERSONAS when that many clear the floor, but never force one below it.
# 30 cleanly separates real matches from non-matches on BOTH score scales: the LLM
# (primary) scores non-matches 0-20 and real fits 45+, so 30-40 behave identically
# there; the deterministic fallback is compressed (real fits ~40-80, non-matches
# ~18-34), where 30 keeps genuine secondaries that a higher floor would wrongly cut.
PERSONA_SELECT_FLOOR = 30.0

# Below this advertiser confidence we ask clarifying questions instead of
# generating a campaign.
CONFIDENCE_THRESHOLD = 0.45

# Map a price positioning to an order-value band (USD). These bands are DERIVED
# from the real catalog distribution (publisher avg_order_value $28-$198 +
# income_tier, persona typical_aov $48-$145 + price_sensitivity), not guessed:
#   value ← high price-sensitivity personas + mid-income low-AOV publishers
#   premium ← low price-sensitivity personas + high-income top-AOV publishers
#   luxury ← ABOVE the catalog ceiling (richest persona $145, richest pub $198):
#            no audience's typical order reaches here, so it is flagged as a gap.
# Used by the deterministic matchers and by derive_economics() (src/derivation.py).
POSITIONING_AOV_BAND = {
    "value": (20, 60),
    "mid": (50, 90),
    "mid-premium": (90, 130),
    "premium": (130, 200),
    "luxury": (200, 10_000),   # above every audience's capacity -> affordability gap
    "unknown": (0, 10_000),    # no penalty when we don't know
}

# Positioning -> the persona price_sensitivity tier this product should target
# (mirrors persona.price_sensitivity vocabulary). Lets Step 2 join product price
# intent to the right shoppers deterministically.
POSITIONING_TO_TARGET_SENSITIVITY = {
    "value": "high",
    "mid": "medium",
    "mid-premium": "medium",
    "premium": "low",
    "luxury": "low",
    "unknown": None,
}

# Cues (seen in subcategories / values / USP / audience) that imply a gifting
# season -> mirrors publisher `notes` gifting-uplift. Deterministic, additive.
SEASONALITY_CUES = {
    "gifting": ["gift", "gifting", "gift-ready", "holiday", "christmas",
                "wedding", "birthday", "present"],
}

# --- Persona scoring weights (must sum to 1.0) ---
PERSONA_WEIGHTS = {
    "affinity": 0.45,    # category_affinities vs the advertiser
    "messaging": 0.30,   # does the persona want the message this brand sends?
    "price": 0.15,       # price_sensitivity vs positioning
    "aov": 0.10,         # typical persona spend vs the publisher band
}

# If the advertiser hits something a persona is "disinterested_in", we don't
# drop them entirely (they might still convert), but we strongly demote them.
PERSONA_DISINTEREST_MULTIPLIER = 0.4

# --- Campaign economics (the brief supplies no budget/CPA, so these are
# clearly-labeled, DERIVED suggestions, surfaced as `assumptions` in the output).
# Everything scales from the product's order value (AOV) + positioning, not flats. ---
DEFAULT_GEOS = ["US-East", "US-West"]
TARGET_CPA_FRACTION_OF_AOV = 0.30   # CPA = 30% of AOV -> implied ROAS ~3.3x

# Conversion rate is driven by CATEGORY (and whether the item is high-ticket),
# NOT by a "premium/mid" label — a $300 premium dog food still converts like pet
# food, only a genuinely expensive item converts like luxury. Grounded in 2024
# e-commerce benchmarks (see CVR_SOURCE); surfaced as an assumption in the output.
CVR_BY_CATEGORY = {
    "groceries": 0.045, "beverages": 0.045, "meal_kits": 0.035,
    "beauty": 0.040, "wellness_dtc": 0.030, "wellness_services": 0.025,
    "apparel": 0.028, "pet": 0.025, "home": 0.014, "software": 0.020,
}
DEFAULT_CVR = 0.025
# Above this order value the purchase is "high-ticket" (rare, highly considered),
# so CVR collapses toward the luxury rate regardless of category (a $1,200 bag).
HIGH_TICKET_THRESHOLD_USD = 500.0
LUXURY_CVR = 0.012
CVR_SOURCE = ("2024 e-commerce benchmarks (Oberlo / Statista): food & beverage ~3-6%, "
              "beauty ~4.5%, apparel ~3%, pet ~2.5%, home & furniture / luxury ~1.2%")

# Assumed display click-through rate, to convert spend -> clicks -> impressions.
DEFAULT_CTR = 0.008
# Default campaign length (for the lifetime/total budget).
DEFAULT_FLIGHT_DAYS = 30
# How long after a click a conversion still counts (standard DTC window).
ATTRIBUTION_WINDOW_DAYS = 7

# Daily budget is sized to buy this many conversions/day (enough to get signal).
# budget = TARGET_CONVERSIONS_PER_DAY * CPA, so it scales with the product economics.
TARGET_CONVERSIONS_PER_DAY = 15

# Fallbacks when we have no AOV basis at all (e.g. gated/off-catalog input).
DEFAULT_DAILY_BUDGET_USD = 500.0
DEFAULT_TARGET_CPA_USD = 30.0

# --- Creative claim guard ---
# Phrases a creative may only use if the advertiser's own facts contain them.
# Some models read persona preferences ("gift sets") as product facts; on a hit
# we regenerate once, then drop the offending body sentence.
BANNED_CLAIM_PHRASES = [
    "gift set", "gift box", "packag", "gift-ready", "gift ready", "ships",
    "shipping", "lifetime", "the best", "master artisan", "certif",
    # claim types a persona may WANT but the brand must actually state to use.
    # The guard only flags these when they are NOT in the advertiser's own facts,
    # so a genuinely sustainable brand keeps them; others can't fabricate them.
    "supply chain", "transparen", "sustainab", "clinically",
    # internal price-tier vocabulary / meta-price talk — never belongs in ad copy
    # (describes the product instead of selling it). "mid-premium" etc. are our enum.
    "mid-premium", "mid premium", "priced thoughtfully", "thoughtfully priced",
    "priced thoroughly", "affordably priced",
]
