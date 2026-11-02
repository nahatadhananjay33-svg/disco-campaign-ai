# Campaign config (`campaign.json`) — every field, its source, and why it matters

The config is the hand-off a real ad system would ingest to actually *run* the
campaign. Each field is sourced from one of three places — the **advertiser profile
(Step 1 LLM)**, the **recommended publishers**, the **selected personas** — or is
**derived** from the product economics. Nothing is a silent guess: every assumed
number is also written in plain English in `assumptions`.

## The economic chain (how the money numbers are derived)

```
AOV   = stated price  → else recommended publishers' average order value
CPA   = 30% × AOV                 (willing to pay ~1/3 of order value to acquire → ~3.3× ROAS)
CVR   = category benchmark        (→ luxury rate only if the item is high-ticket, ≥ $500)
CPC   = CPA × CVR                 (a click is worth its conversion chance × the CPA)
budget/day = 15 target conversions × CPA
```

**Why CVR is by category, not by "premium/mid":** conversion rate is driven by *what*
you're buying and *how expensive/considered* it is — not by a positioning label. A
$300 premium dog food still converts like pet food (~2.5%); only a genuinely
expensive item (a $1,200 handbag) converts like luxury (~1.2%). Grounded in 2024
e-commerce benchmarks (Oberlo/Statista): food & beverage ~3–6%, beauty ~4.5%,
apparel ~3%, pet ~2.5%, home/luxury ~1.2%.

## Field-by-field

### Identity & lifecycle
| Field | Source | Why it matters |
|--|--|--|
| `campaign_id` | generated | unique id so logged results can be **joined back** to this exact plan (essential for training). |
| `created_at` | generated | audit trail for when the plan was produced. |
| `status` | constant `draft` | a recommendation, not a live campaign — a human approves before launch. |

### Objective & category
| Field | Source | Why it matters |
|--|--|--|
| `objective` | Step 1 `business_model` | conversions for DTC, lead_generation for B2B — sets what the system optimizes toward. |
| `advertiser_category` | Step 1 `product_category` | the campaign's vertical; drives CVR and reporting. |

### Targeting — *who* sees the ad
| Field | Source | Why it matters |
|--|--|--|
| `personas` | Step 2 selected personas | the audience segments to serve; each gets its own creative. Precise segments = higher CVR, less wasted spend. |
| `interests` | Step 1 subcategories + USP | interest keywords the ad platform targets on. |
| `geographies` | recommended publishers' `top_geos` | where to serve; avoids spend on regions you can't fulfill. |
| `age_range` | Step 1 `target_age_range` | demographic narrowing — don't pay to reach the wrong life-stage. |
| `gender` | Step 1 `target_gender` | for gendered products, halves wasted impressions. |

### Publishers — *where* the ad runs
| Field | Source | Why it matters |
|--|--|--|
| `publisher_id` / `name` | Step 2 ranked publishers | the placements, best-fit first. |
| `budget_percentage` | ∝ match score | more budget to better-fitting audiences → better blended CVR. Sums to 100. |

### Budget — *how much* to spend
| Field | Source | Why it matters |
|--|--|--|
| `daily_budget` | 15 × CPA (derived) | sized to buy enough conversions/day for signal; scales with the product's economics, not a flat default. |
| `total_budget` | daily × flight (derived) | the lifetime cap a real campaign needs. |
| `flight_days` | assumption (30) | campaign length; makes the total meaningful. |
| `pacing` | constant "even" | spend the daily budget evenly through the day (vs front-loading). |
| `basis` | constant "assumption" | flags that we set this, the advertiser didn't. |

### Bid strategy — *how* to buy
| Field | Source | Why it matters |
|--|--|--|
| `target_cpa_usd` | 30% × AOV (derived) | the most you'll pay per acquisition while staying profitable (~3.3× ROAS). |
| `suggested_cpc_range_usd` | CPA × CVR, ±20% | what to bid per click, grounded in the conversion rate. |
| `aggressiveness` | personas' `price_sensitivity` | low-sensitivity audiences convert even at higher bids → bid up; value audiences → tighten. |
| `rationale` | derived | one-line justification a human can sanity-check. |

### Forecast — *what the spend buys* (makes it a real plan)
| Field | Source | Why it matters |
|--|--|--|
| `estimated_cvr` | category benchmark (+ high-ticket rule) | the key assumption behind all economics — made explicit and auditable. |
| `cvr_basis` | the benchmark source | shows the number isn't invented. |
| `target_conversions_per_day` | assumption (15) | the volume the budget is sized for. |
| `estimated_clicks_per_day` | budget ÷ CPC | the traffic the budget buys. |
| `estimated_impressions_per_day` | clicks ÷ CTR | reach needed to hit those clicks. |
| `available_monthly_impressions` | recommended publishers' `monthly_impressions` | the inventory pool — can the audience even absorb the spend? (small premium audiences can't). |
| `expected_roas` | AOV ÷ CPA | the profitability headline: revenue per ad dollar. |

### Measurement — *how success is defined*
| Field | Source | Why it matters |
|--|--|--|
| `conversion_event` | derived (purchase / lead) | what counts as a conversion — without it CVR/CPA are undefined. |
| `attribution_window_days` | assumption (7) | how long after a click a conversion still counts; shapes the measured CVR. |
| `optimization_goal` | constant `minimize_cpa` | what the system tunes toward. |
| `kpi_targets {target_cpa, target_roas}` | derived | the explicit bar the campaign is judged against. |

### Feedback — *predicted vs actual* (the data flywheel)
| Field | Source | Why it matters |
|--|--|--|
| `predicted {cvr, cpa, conversions, roas}` | derived | what this plan forecasts. |
| `actual {…}` | null until launch | filled with real results post-launch. **The predicted-vs-actual gap — per publisher and persona — is the training label** that moves the system from zero-shot LLM to a learned ranker. This is the single most important field for "how do we improve the model." |

### Creatives — *what* the ad says
| Field | Source | Why it matters |
|--|--|--|
| `persona_id` / `name` / `headline` | Step 3 | ties each tailored creative to the segment it runs for — the full who/where/what loop in one config. |

### Assumptions
Every derived number (CPA, CVR, CPC, budget, flight, CTR, reach) is restated here in
plain English with its basis, so a human reviewer can challenge or override any single
assumption without reading the code.

## Honest limitations (what we'd improve with data / time)
- **CVR** is a category benchmark, not a per-publisher learned rate; with conversion
  data it becomes a trained per-segment estimate.
- **CTR (0.8%)** and **target conversions/day (15)** are reasoned defaults, tunable in
  `config.py`.
- Premium/luxury audiences are smaller, so the daily budget should be **capped to
  actual reach** in production (we surface the available impression pool to enable that).
