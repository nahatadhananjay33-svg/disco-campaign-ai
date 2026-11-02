# Step 4 — full campaign.json per example, every field with reasoning


## #1 — We sell premium dog food for senior dogs, targeting owners who care about joint health and longevity. Grain-free, vet-formulated, subscription-based.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_pet_432f2f46` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `pet` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_004, persona_002, persona_005 | matched shopper segments; each gets its own creative |
| `interests` | pet_food, senior, grain_free, vet_formulated, subscription, premium dog food for senior dogs | interest keywords (from subcats + USP) to target on |
| `geographies` | nationwide, US-West, US-South | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 25-55 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | all | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Ruffco | 34% | share proportional to its Step-2 match score |
| Pawline | 34% | share proportional to its Step-2 match score |
| Tailcrate | 32% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $258 | 15 target conversions/day × $17 CPA |
| `total_budget` | $7740 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $17 | $17 = 30% of the recommended publishers' average order value (no price stated) ($57); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $0.34–0.52 | CPA × CVR ($17 × 2.5%), ±20% |
| `aggressiveness` | `aggressive` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 2.5% | 'pet' category benchmark |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 600 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 75,000 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 75,200,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $17 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 2.5%, cpa $17, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Pet Parent | Vet‑Formulated, Grain‑Free Meals for Senior Dogs |
| The Busy Parent | Feed Your Senior Dog the Same Care Parents Trust |
| The Affluent Classic | A Legacy of Care for Your Senior Companion |

## #2 — A sustainable activewear brand for women. Made from recycled ocean plastic. Price point sits between Lululemon and Girlfriend Collective.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_apparel_78430d32` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `apparel` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_006, persona_009, persona_001, persona_003, persona_008 | matched shopper segments; each gets its own creative |
| `interests` | activewear, made from recycled ocean plastic, sustainable activewear for women, price point between Lululemon and Girlfriend Collective | interest keywords (from subcats + USP) to target on |
| `geographies` | US-West, US-South, US-Northeast, US-Midwest | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 18-45 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | female | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Movewell | 24% | share proportional to its Step-2 match score |
| Stride & Stem | 22% | share proportional to its Step-2 match score |
| Everbody | 19% | share proportional to its Step-2 match score |
| Cloudfoot | 18% | share proportional to its Step-2 match score |
| Studiogrid | 17% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $360 | 15 target conversions/day × $24 CPA |
| `total_budget` | $10800 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $24 | $24 = 30% of the advertiser's stated product price ($80); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $0.54–0.80 | CPA × CVR ($24 × 2.8%), ±20% |
| `aggressiveness` | `balanced` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 2.8% | 'apparel' category benchmark |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 537 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 67,125 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 52,200,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $24 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 2.8%, cpa $24, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Sustainability Buyer | From Ocean to Studio: Recycled‑Plastic Performance |
| The Fitness Enthusiast | Move with Purpose: Ocean‑Plastic Activewear |
| The Wellness Optimizer | Move with Purpose: Recycled Ocean‑Plastic Activewear |
| The Gen Z Aesthete | Turn Waves into Workouts |
| The Value-Conscious Shopper | Upgrade your activewear rotation for less |

## #3 — We make a non-alcoholic sparkling drink with adaptogens. It's for people who want to feel good without a hangover, kind of like a functional cocktail alternative.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_beverages_aaab4f51` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `beverages` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_001, persona_009, persona_003, persona_006 | matched shopper segments; each gets its own creative |
| `interests` | functional_beverages, sparkling, non_alcoholic, adaptogens, soda_alternative, contains adaptogens | interest keywords (from subcats + USP) to target on |
| `geographies` | US-West, US-Northeast | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 21-45 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | all | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Pop & Sip | 40% | share proportional to its Step-2 match score |
| Pantrygood | 31% | share proportional to its Step-2 match score |
| Daily Form | 29% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $249 | 15 target conversions/day × $17 CPA |
| `total_budget` | $7470 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $17 | $17 = 30% of the recommended publishers' average order value (no price stated) ($55); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $0.60–0.90 | CPA × CVR ($17 × 4.5%), ±20% |
| `aggressiveness` | `balanced` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 4.5% | 'beverages' category benchmark |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 332 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 41,500 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 19,800,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $17 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 4.5%, cpa $17, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Wellness Optimizer | Sparkle Your Recovery with Adaptogenic Power |
| The Fitness Enthusiast | Sparkling Recovery for the Workout Warrior |
| The Gen Z Aesthete | Sparkle Your Vibe—Adaptogen‑Infused, Hangover‑Free Sips |
| The Sustainability Buyer | Sparkling Adaptogen Refreshment for the Mindful Shopper |

## #4 — Small-batch candles poured by hand in Vermont. Natural soy wax, no synthetic fragrances. Mostly bought as gifts.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_home_f91e00da` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `home` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_010, persona_006, persona_003, persona_005, persona_001 | matched shopper segments; each gets its own creative |
| `interests` | candles, home_fragrance, gifting, small-batch, poured by hand in Vermont, natural soy wax | interest keywords (from subcats + USP) to target on |
| `geographies` | US-West, US-Northeast | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 25-55 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | all | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Hearthstone Goods | 51% | share proportional to its Step-2 match score |
| Northbed | 49% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $814 | 15 target conversions/day × $54 CPA |
| `total_budget` | $24435 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $54 | $54 = 30% of the recommended publishers' average order value (no price stated) ($181); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $0.61–0.91 | CPA × CVR ($54 × 1.4%), ±20% |
| `aggressiveness` | `aggressive` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 1.4% | 'home' category benchmark |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 1,072 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 134,000 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 6,400,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $54 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 1.4%, cpa $54, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Gifter | Hand‑Poured Vermont Candles: Gift‑Ready Elegance |
| The Sustainability Buyer | Home goods crafted for clean-burning rituals |
| The Gen Z Aesthete | Vermont‑Poured Candles: Your Cozy, Small‑Batch Glow |
| The Affluent Classic | A Hand‑Poured Vermont Candle for Your Home |
| The Wellness Optimizer | Hand‑Poured Vermont Candles for Your Wellness Routine |

## #6 — Technical outerwear for serious backcountry skiers. Our shells are what patrollers wear. Starts at $650, goes up from there.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_apparel_f110d5dd` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `apparel` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_009, persona_001, persona_006, persona_005, persona_010 | matched shopper segments; each gets its own creative |
| `interests` | outerwear, shells, activewear, ski_wear, mens, women | interest keywords (from subcats + USP) to target on |
| `geographies` | US-West, US-Northeast, US-South | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 25-50 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | all | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Cloudfoot | 24% | share proportional to its Step-2 match score |
| Movewell | 23% | share proportional to its Step-2 match score |
| Linden Park | 19% | share proportional to its Step-2 match score |
| Marlowe & Co. | 17% | share proportional to its Step-2 match score |
| Stride & Stem | 17% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $2925 | 15 target conversions/day × $195 CPA |
| `total_budget` | $87750 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $195 | $195 = 30% of the advertiser's stated product price ($650); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $1.87–2.81 | CPA × CVR ($195 × 1.2%), ±20% |
| `aggressiveness` | `aggressive` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 1.2% | high-ticket item ($650 >= $500), converts at the luxury rate |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 1,250 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 156,250 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 45,600,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $195 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 1.2%, cpa $195, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Fitness Enthusiast | Patroller‑Grade Outerwear for the Serious Athlete |
| The Wellness Optimizer | Elevate Your Performance with Technical Outerwear |
| The Sustainability Buyer | Gear That Endures—Like Your Values |
| The Affluent Classic | Backcountry‑Grade Outerwear for the Classic Trail |
| The Gifter | Gift the Edge of Backcountry Performance |

## #7 — B2B SaaS for dental practices. We automate their patient recall workflow.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_software_746360a2` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `lead_generation` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `software` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_002, persona_007, persona_001, persona_005, persona_006 | matched shopper segments; each gets its own creative |
| `interests` | saas, b2b, dental_software, workflow_automation, automates patient recall workflow | interest keywords (from subcats + USP) to target on |
| `geographies` | US-West, US-Northeast, US-East, US-Midwest | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | None | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | None | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Cloudfoot | 40% | share proportional to its Step-2 match score |
| Swiftcart | 30% | share proportional to its Step-2 match score |
| Studiogrid | 30% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $282 | 15 target conversions/day × $19 CPA |
| `total_budget` | $8460 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $19 | $19 = 30% of the recommended publishers' average order value (no price stated) ($63); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $0.30–0.46 | CPA × CVR ($19 × 2.0%), ±20% |
| `aggressiveness` | `aggressive` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 2.0% | 'software' category benchmark |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 742 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 92,750 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 103,400,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `lead` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $19 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 2.0%, cpa $19, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Busy Parent | Never Miss a Patient Appointment Again |
| The Convenience-First Millennial | One-Click Patient Reminders, Like Your Favorite Meal Kit |
| The Wellness Optimizer | Optimize Your Dental Practice Like Your Body |
| The Affluent Classic | Patient Recall as Reliable as a Classic Timepiece |
| The Sustainability Buyer | Cut Paper Waste, Boost Recall Efficiency |

## #9 — Refillable, concentrated cleaning products. Skip the single-use plastic bottles. Works as well as the big brands. We want to show up where people who already care about sustainability are checking out.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_home_22887f14` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `home` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_006, persona_002, persona_001, persona_008, persona_005 | matched shopper segments; each gets its own creative |
| `interests` | cleaning, household, refillable, sustainable, concentrated cleaning products, skips single-use plastic bottles | interest keywords (from subcats + USP) to target on |
| `geographies` | US-West, US-Northeast | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 25-55 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | all | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Hearthstone Goods | 51% | share proportional to its Step-2 match score |
| Northbed | 49% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $814 | 15 target conversions/day × $54 CPA |
| `total_budget` | $24435 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $54 | $54 = 30% of the recommended publishers' average order value (no price stated) ($181); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $0.61–0.91 | CPA × CVR ($54 × 1.4%), ±20% |
| `aggressiveness` | `balanced` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 1.4% | 'home' category benchmark |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 1,072 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 134,000 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 6,400,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $54 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 1.4%, cpa $54, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Sustainability Buyer | Clean Like Big Brands, Waste Like Zero |
| The Busy Parent | Streamline your household cleaning routine |
| The Wellness Optimizer | Optimize your home system with concentrated clean ingredients |
| The Value-Conscious Shopper | Upgrade your household routine for less waste |
| The Affluent Classic | Elevate your home goods with zero-waste cleaning |

## #10 — Custom-fit leather handbags, Italian-made, handcrafted in Florence. Minimum order ships in 6 weeks. Average price point $1,200.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_apparel_4a8d7268` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `apparel` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_005, persona_010, persona_001, persona_006 | matched shopper segments; each gets its own creative |
| `interests` | handbags, leather_goods, accessories, luxury, custom-fit, Italian-made | interest keywords (from subcats + USP) to target on |
| `geographies` | US-Northeast, US-South, US-West, US-Midwest | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 30-55 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | female | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Linden Park | 23% | share proportional to its Step-2 match score |
| Marlowe & Co. | 21% | share proportional to its Step-2 match score |
| Stride & Stem | 20% | share proportional to its Step-2 match score |
| Movewell | 19% | share proportional to its Step-2 match score |
| Everbody | 17% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $5400 | 15 target conversions/day × $360 CPA |
| `total_budget` | $162000 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $360 | $360 = 30% of the advertiser's stated product price ($1200); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $3.46–5.18 | CPA × CVR ($360 × 1.2%), ±20% |
| `aggressiveness` | `aggressive` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 1.2% | high-ticket item ($1200 >= $500), converts at the luxury rate |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 1,250 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 156,250 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 47,400,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $360 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 1.2%, cpa $360, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Affluent Classic | Timeless leather goods for your next journey |
| The Gifter | Give the extraordinary, presented in custom wrap |
| The Wellness Optimizer | Engineered for daily performance and design |
| The Sustainability Buyer | Handcrafted leather designed to last |

## #11 — We sell protein bars that don't taste like cardboard. That's basically the whole pitch.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_groceries_ea40f204` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `groceries` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_009, persona_001, persona_006, persona_002, persona_008 | matched shopper segments; each gets its own creative |
| `interests` | protein_bars, snacks, nutrition_bars, food, good taste, protein bars that don't taste like cardboard | interest keywords (from subcats + USP) to target on |
| `geographies` | US-West, US-Northeast, US-East, US-Midwest, nationwide | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 18-45 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | all | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Pantrygood | 21% | share proportional to its Step-2 match score |
| Swiftcart | 21% | share proportional to its Step-2 match score |
| Pop & Sip | 20% | share proportional to its Step-2 match score |
| Kitchenly | 20% | share proportional to its Step-2 match score |
| Daily Form | 18% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $241 | 15 target conversions/day × $16 CPA |
| `total_budget` | $7236 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $16 | $16 = 30% of the recommended publishers' average order value (no price stated) ($54); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $0.58–0.86 | CPA × CVR ($16 × 4.5%), ±20% |
| `aggressiveness` | `balanced` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 4.5% | 'groceries' category benchmark |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 335 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 41,875 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 139,800,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $16 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 4.5%, cpa $16, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Fitness Enthusiast | Fuel your next PR without the cardboard aftertaste. |
| The Wellness Optimizer | Fuel your wellness routine without the cardboard taste |
| The Sustainability Buyer | Protein bars that don't taste like cardboard |
| The Busy Parent | Snacks for when your meal kit fails |
| The Value-Conscious Shopper | Protein bars that actually taste good |

## #12 — A subscription box for new cat owners. First three months of their cat's life. Toys, food samples, a little booklet about what to expect.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_pet_b471ed21` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `pet` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_004, persona_010, persona_002, persona_007 | matched shopper segments; each gets its own creative |
| `interests` | subscription, pet_supplies, pet_food, toys, gifting, curated for the first three months of a kitten's life | interest keywords (from subcats + USP) to target on |
| `geographies` | nationwide, US-West, US-South | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 21-50 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | all | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Ruffco | 35% | share proportional to its Step-2 match score |
| Pawline | 33% | share proportional to its Step-2 match score |
| Tailcrate | 32% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $258 | 15 target conversions/day × $17 CPA |
| `total_budget` | $7740 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $17 | $17 = 30% of the recommended publishers' average order value (no price stated) ($57); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $0.34–0.52 | CPA × CVR ($17 × 2.5%), ±20% |
| `aggressiveness` | `aggressive` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 2.5% | 'pet' category benchmark |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 600 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 75,000 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 75,200,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $17 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 2.5%, cpa $17, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Pet Parent | Welcome your new kitten with expert guidance |
| The Gifter | curated for the first three months of a kitten's life |
| The Busy Parent | Simplify your kitten's first three months |
| The Convenience-First Millennial | Like your favorite meal kit, but for your new kitten |

## #13 — Workout supplements: pre-workout, creatine, protein. We compete on price, not on marketing. Same formulations as the expensive brands for half the cost.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_wellness_dtc_2017e2dc` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `wellness_dtc` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_009, persona_001, persona_008 | matched shopper segments; each gets its own creative |
| `interests` | supplements, pre_workout, creatine, protein, fitness, same formulations as expensive brands for half the cost | interest keywords (from subcats + USP) to target on |
| `geographies` | US-West, US-Northeast, US-South | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 18-40 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | all | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Daily Form | 23% | share proportional to its Step-2 match score |
| Pop & Sip | 21% | share proportional to its Step-2 match score |
| Studiogrid | 20% | share proportional to its Step-2 match score |
| Movewell | 18% | share proportional to its Step-2 match score |
| Pantrygood | 18% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $257 | 15 target conversions/day × $17 CPA |
| `total_budget` | $7722 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $17 | $17 = 30% of the recommended publishers' average order value (no price stated) ($57); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $0.41–0.61 | CPA × CVR ($17 × 3.0%), ±20% |
| `aggressiveness` | `balanced` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 3.0% | 'wellness_dtc' category benchmark |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 505 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 63,125 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 55,400,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $17 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 3.0%, cpa $17, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Fitness Enthusiast | Fuel your recovery with pure performance |
| The Wellness Optimizer | Optimize your routine with clinical-grade supplements. |
| The Value-Conscious Shopper | Stop overpaying for pre-workout and protein |

## #14 — Bedding. Linen. Actually-breathable stuff made in Portugal. Our customers are mostly people who got tired of the Brooklinen/Parachute aesthetic and want something a little more grown-up.

### Identity & lifecycle
| Field | Value | Why this value |
|--|--|--|
| `campaign_id` | `camp_home_d984c891` | unique id so logged results can be joined back to this plan |
| `created_at` | `2026-11-02T10:31:40+00:00` | when the plan was generated (audit trail) |
| `status` | `draft` | a plan, not live — needs human approval before launch |

### Objective & category
| Field | Value | Why this value |
|--|--|--|
| `objective` | `conversions` | conversions for DTC / lead_generation for B2B — what the system optimizes toward |
| `advertiser_category` | `home` | the vertical; drives the CVR benchmark and reporting |

### Targeting — *who* sees the ad
| Field | Value | Why this value |
|--|--|--|
| `personas` | persona_005, persona_006, persona_010, persona_003, persona_001 | matched shopper segments; each gets its own creative |
| `interests` | bedding, linen, home_textiles, actually breathable linen, made in Portugal, grown-up alternative to mainstream brands | interest keywords (from subcats + USP) to target on |
| `geographies` | US-Northeast, US-West | the recommended publishers' top geos; don't serve where unfulfillable |
| `age_range` | 30-55 | the advertiser's intended age (distinct from a publisher's audience skew) |
| `gender` | all | the advertiser's intended gender; avoids wasted impressions on gendered products |

### Publishers — *where* (budget split ∝ match score)
| Publisher | Budget % | Why |
|--|--|--|
| Northbed | 52% | share proportional to its Step-2 match score |
| Hearthstone Goods | 48% | share proportional to its Step-2 match score |

### Budget — *how much*
| Field | Value | Why this value |
|--|--|--|
| `daily_budget` | $814 | 15 target conversions/day × $54 CPA |
| `total_budget` | $24435 | daily × 30-day flight (lifetime cap) |
| `flight_days` | 30 | assumed campaign length |
| `pacing` | `even` | spend the daily budget evenly through the day |
| `basis` | `assumption` | flags that we set this — the advertiser gave no budget |

### Bid strategy — *how* to buy
| Field | Value | Why this value |
|--|--|--|
| `target_cpa_usd` | $54 | $54 = 30% of the recommended publishers' average order value (no price stated) ($181); implied ROAS ~3.3x |
| `suggested_cpc_range_usd` | $0.61–0.91 | CPA × CVR ($54 × 1.4%), ±20% |
| `aggressiveness` | `aggressive` | from the audience's price-sensitivity — low-sensitivity → bid up |

### Forecast — *what the spend buys*
| Field | Value | Why this value |
|--|--|--|
| `estimated_cvr` | 1.4% | 'home' category benchmark |
| `target_conversions_per_day` | 15 | the volume the budget is sized for |
| `estimated_clicks_per_day` | 1,072 | daily budget ÷ CPC |
| `estimated_impressions_per_day` | 134,000 | clicks ÷ assumed 0.8% display CTR |
| `available_monthly_impressions` | 6,400,000 | inventory pool across recommended publishers — can the audience absorb the spend? |
| `expected_roas` | 3.3x | AOV ÷ CPA — revenue per ad dollar |

### Measurement — *how success is defined*
| Field | Value | Why this value |
|--|--|--|
| `conversion_event` | `purchase` | what counts as a conversion |
| `attribution_window_days` | 7 | how long after a click a conversion still counts |
| `optimization_goal` | `minimize_cpa` | what the system tunes toward |
| `kpi_targets` | CPA $54 / ROAS 3.3x | the bar the campaign is judged against |

### Feedback — *predicted vs actual (training data)*
| Field | Value | Why this value |
|--|--|--|
| `predicted` | cvr 1.4%, cpa $54, 15/day, roas 3.3x | what this plan forecasts |
| `actual` | null | filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker |

### Creatives — *what it says* (one per persona)
| Persona | Headline |
|--|--|
| The Affluent Classic | Invest in heritage European home goods |
| The Sustainability Buyer | Upgrade your home goods with European-made linen |
| The Gifter | Give the home goods gift they will actually use |
| The Gen Z Aesthete | Home decor that looks like your mood board |
| The Wellness Optimizer | Upgrade your sleep architecture with real linen. |
