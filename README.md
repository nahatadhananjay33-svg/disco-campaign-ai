# Disco Campaign AI

An advertiser describes their business in a sentence or two. The product hands back a
**ready-to-review campaign**:

1. **Ranked publishers** — where to advertise, each with a reason, plus the ones we ruled
   out and why.
2. **Up to 5 ad creatives** — one per shopper persona worth targeting, written in that
   persona's voice, with the thinking shown.
3. **A campaign config** — targeting, budget split, bid strategy, and a forecast a human
   can review and launch.

It behaves like a careful strategist, not a demo: it **asks** instead of guessing when the
input is vague, says **"no good fit"** instead of forcing a match when the catalog doesn't
suit the advertiser, and keeps working even if the AI is briefly down.

**Live demo:** https://disco-campaign-ai.streamlit.app/

## Run it

A standard Python + Streamlit app — **no Docker needed**. Python 3.13 recommended.

```bash
# 1 · clone
git clone https://github.com/nahatadhananjay33-svg/disco-campaign-ai.git
cd disco-campaign-ai

# 2 · (recommended) a clean virtual environment
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate

# 3 · install dependencies
pip install -r requirements.txt

# 4 · configure the environment — add a free Groq key
cp .env.example .env              # Windows: copy .env.example .env
#   then open .env and paste your key from console.groq.com/keys

# 5 · run
pytest -q                         # 132 tests, no API key needed
streamlit run app.py              # opens http://localhost:8501
```

- `GROQ_API_KEY` (required) — the AI behind understanding, matching, and creatives.
- `GEMINI_API_KEY` (optional) — a backup AI: if Groq fails, the same calls retry on Gemini.

Prefer not to install anything? The live demo runs this exact code:
**https://disco-campaign-ai.streamlit.app/**

## How it works

```mermaid
%%{init: {"flowchart": {"defaultRenderer": "elk"}}}%%
flowchart TD
    A([Advertiser sentence]) -->|LLM parse| B[Advertiser profile]
    B --> C{Confidence high enough?}
    C -->|no| STOP[Ask clarifying questions · stop]
    C -->|yes| PUB["Match publishers · LLM<br/>➜ 3–4 ideal publishers + exclusions"]
    C -->|yes| PER["Match personas · LLM<br/>➜ 3–5 best-fit personas"]
    PUB --> COV{Coverage ok?}
    COV -->|none| GAP[Explain the gap · no campaign]
    COV -->|good / weak| CFG
    PER --> CFG
    PER --> CRE

    subgraph OUT ["Final output — what the advertiser gets"]
      CFG["Campaign config<br/>from profile + publishers + personas"]
      CRE["Creatives<br/>from profile + persona"]
    end

    classDef stop fill:#fde8e8,stroke:#e57373,color:#111;
    classDef out fill:#e8f0fe,stroke:#5b8def,color:#111,stroke-width:2px;
    classDef win fill:#e4f6e4,stroke:#43a047,stroke-width:2px,color:#111;
    class STOP,GAP stop
    class CRE,CFG out
    class PUB,PER win
    style OUT fill:#f3f7ff,stroke:#5b8def,stroke-dasharray:4 3
```

Five decisions. Each reads specific inputs and produces a specific output:

**1 · Understand the advertiser.**
*In:* the raw sentence. *Out:* an **18-field profile** — product category & subcategories,
price point & positioning, target audience (age / gender / geography), USPs, values, brand
tone, business model, and an expected order value.
If the sentence is too thin to fill these confidently, the product **stops and asks**
rather than inventing a campaign. *("idk just try it" → asks what you actually sell.)*

**2 · Pick the publishers.**
*In:* the profile + all 20 publishers (audience, income tier, average order value, reach).
*Out:* every publisher scored 0–100 with a one-line reason, poor fits marked **excluded**.
The call is audience fit — a $1,200 handbag brand should land on the affluent,
high-order-value publisher, not the budget one.

**3 · Pick the personas.**
*In:* the profile + all 10 personas (category affinities, price sensitivity, typical spend,
what they dislike). *Out:* each persona scored with a reason; the strongest (up to 5) are
selected. A persona that's *put off* by the advertiser's positioning is pushed down — we
don't target people the product would turn off.

**4 · Write the creatives.**
*In:* the profile + each selected persona. *Out:* one headline + body per persona, in that
persona's language, with the reasoning shown. A guard strips any claim the advertiser never
made, so the copy never oversells.

**5 · Build the campaign config.**
*In:* the profile + recommended publishers + selected personas. *Out:* targeting, a budget
split weighted by fit, a bid strategy, and a deliverability forecast — every number derived
(see *The numbers*), none guessed.

## The matching logic — why it picks what it picks

Matching is a judgment, not keyword overlap, so this is where the product uses the most
business sense. It weighs the fields in a deliberate order:

- **Category / affinity first.** If the audience doesn't shop the category, nothing else
  matters — so this dominates the score.
- **Then message & audience fit** — does the publisher's audience and the persona's taste
  line up with the brand's positioning and values.
- **Then price alignment** — a premium brand belongs with low-price-sensitivity shoppers
  and high-order-value publishers; a value brand with the opposite.
- **Order value counts least** — people buy everyday products regardless of basket size, so
  AOV nudges the ranking rather than driving it.

These priorities are deliberate **priors**, not weights learned from data (there's no
campaign history yet) — which is exactly why the AI, reading all the fields together, makes
the call and shows its reason, so you can trust it or override it.

## The numbers — grounded, not guessed

Every figure traces to a real input or a cited benchmark:

- **Order value (AOV)** — the advertiser's stated price if given, else the average of the
  recommended publishers, else the personas' typical spend. Never a made-up midpoint.
- **Cost per acquisition = 30% of order value** — a **working assumption** (implies ~3.3x
  ROAS), not a proven constant; it's flagged as an assumption in every output for a human to
  confirm.
- **Conversion rate by category** — grounded in 2024 e-commerce conversion benchmarks by
  industry ([Oberlo](https://www.oberlo.com/statistics/ecommerce-conversion-rate-by-industry)):
  groceries/beverages ~4.5%, beauty ~4%, wellness ~3%, apparel ~2.8%, pet ~2.5%, home ~1.4%,
  high-ticket (≥ $500) ~1.2%. A $60 dog-food order and a $1,200 handbag don't convert alike.
- **Budget, clicks, impressions, ROAS** follow from those, and the forecast is checked
  against the publishers' real available inventory so the plan is physically deliverable.

## Always-on (the fallback)

Each AI step has a simple rule-based backup, so a single outage degrades the output instead
of crashing it.
- **Benefit:** the product always returns a valid, usable campaign — and the full test suite
  runs with no API key at all.
- **Trade-off:** in backup mode the matching is rule-based, so blunter than the AI's
  reasoning. That's why the AI is the default and the backup only catches it when it falls.

## What's genuinely hard here (and what isn't)

The easy part was the **design** — sketching the pipeline and deciding the shape of the output.

The hard part, honestly, was giving that design **business judgment**: which fields matter,
how much each should weigh, and reasoning about a buyer the way a strategist would. I don't
come from an ad-tech background, so I had to research and reason it out myself — price
sensitivity, buyer behaviour, order value, income tiers — and *then* teach the AI to apply
the same judgment. Getting a model to think "this field means this, for this shopper" was
the toughest part by far.

One concrete example: for a pet brand, the best persona to target had only a **mid-range
income** — on price alone it looked weak. But the attributes together made it the right
call, and the deciding one was that these shoppers are **repeat buyers** — their
repeat-purchase behaviour keeps generating revenue, which matters more than a single basket
size. Working out *that* kind of reasoning — and the nuance that a mid/high-income,
lifestyle-driven audience will still buy a premium everyday product even when its order
value is low — is where the real difficulty, and the most room to improve, lives.

## What I'd do next

- **Make the matching scalable.** Today one AI call scores the whole catalog — accurate, but
  it won't hold at thousands of publishers. The immediate next step is **embeddings + AI
  rerank**: embed the catalog once, pull a cheap shortlist by similarity, and let the AI rank
  only that shortlist — same quality, at a fixed cost no matter how big the catalog grows.
- **Then learn from results.** Once real campaigns produce accept/reject and conversion data,
  train a proper ranker (a two-tower retrieval model + a gradient-boosted reranker). The
  system already stores predicted-vs-actual as the training labels; today's AI reasoning is
  what bootstraps it.
- **Sharpen the edges** — improve category→subcategory matching (the cases below), cut the
  AI's latency, and measure and bring down per-campaign cost.
- **Keep improving the business sense** — the field weighting and persona reasoning are the
  heart of the product and have the most room to get smarter.

## What I intentionally cut

- **Breadth, for time.** With ~2–3 days, I chose depth over exploring lots of AI techniques:
  get the business reasoning right and make the AI implement it faithfully, rather than
  half-trying many approaches. It's an honest prototype — strong, not yet a scalable
  production system.
- **A validated CPA.** CPA = 30% of order value (≈3.3x ROAS) is a sensible working
  assumption, not a proven number — so it's labeled an assumption in every output.
- **Some category→subcategory edge cases.** The AI mis-ranked a few (e.g. apparel vs luggage,
  and instant / grocery-delivery). Fixing one case tended to destabilise others, and I didn't
  have time to re-test the whole suite — so I deliberately left 2–3 (there are probably more)
  and kept the stable baseline. Better matching here is on the next list.
- **No trained model, vector search, or logins** — none earn their complexity at this size;
  they're the scaling path, not day-one work.
- **One creative per persona**, not A/B variants, to stay inside the 3–5 the brief asks for.

## Layout

```
app.py          the interface
src/            pipeline, matching, creative, campaign builder, models, config, AI client
prompts/        the AI prompts (understanding, matching, creative)
data/           publishers.json · shopper_personas.json · example_advertisers.txt
tests/          132 offline tests (no API key needed)
docs/           known_limitations.md — edge cases + the path to production
```
