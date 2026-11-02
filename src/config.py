"""All tunable knobs live here, on purpose.

In the interview they may ask us to "change the weighting" live. Because every
weight is one place, that is a one-line edit — not a hunt through the matcher.
These are *design choices*, not learned parameters. In production we would tune
them against real campaign outcomes (see README).
"""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# --- Publisher scoring weights for the DETERMINISTIC FALLBACK matcher (sum to 1.0) ---
# These are HAND-SET PRIORS, not learned parameters: at cold-start there is no
# conversion data to fit them to (that is exactly why the LLM is the primary matcher).
# So what is justified is the ORDERING, from ad-targeting first principles — NOT the
# exact decimals, which are round, deliberate priors:
#   category 0.40    — relevance is THE primary signal. If the audience doesn't shop the
#                      product's category, nothing else matters, so it gets the most weight.
#   subcategory 0.25 — finer relevance within the category (pet_food vs pet_toys).
#   audience 0.15    — demographic alignment (gender, here) refines a good category match.
#   aov 0.10 +       — weakest signals: everyday-category products are bought by that
#   positioning 0.10   category's audience regardless of basket size, and tier is soft,
#                      so neither should outweigh relevance.
# This mirrors how ad platforms rank (intent/category first, audience next, economics
# last). Equal weights were rejected: they would imply AOV matters as much as category,
# which ad targeting says it does not. In production these would be LEARNED from campaign
# outcomes (the feedback loop in the README). The LLM primary matcher ignores them.
PUBLISHER_WEIGHTS = {
    "category": 0.40,
    "subcategory": 0.25,
    "audience": 0.15,
    "aov": 0.10,
    "positioning": 0.10,
}

# A publisher scoring at or below this is shown as "excluded", with a reason.
# On the 0-100 weighted scale that is roughly a third: below it, too few factors
# align to be worth recommending. (A round cutoff, same prior-not-learned caveat.)
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

# --- Persona scoring weights for the DETERMINISTIC FALLBACK matcher (sum to 1.0) ---
# Same reasoning as PUBLISHER_WEIGHTS: hand-set priors justified by their ordering, to
# be learned from data in production.
#   affinity 0.45  — category_affinities vs the advertiser: the primary "would this
#                    shopper even buy this?" signal, so it leads.
#   messaging 0.30 — message-market fit (persona messaging_preferences vs the brand's
#                    tone/USPs). Weighted high because these personas drive the ad COPY.
#   price 0.15     — the persona's price_sensitivity vs the product's positioning.
#   aov 0.10       — typical persona spend vs the band: weakest, a soft economic check.
PERSONA_WEIGHTS = {
    "affinity": 0.45,
    "messaging": 0.30,
    "price": 0.15,
    "aov": 0.10,
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
