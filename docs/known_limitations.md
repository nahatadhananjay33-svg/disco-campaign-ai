# Known limitations & edge cases

An honest record of where the prototype's judgment breaks, why, and what the real fix
is. These are deliberate trade-offs for a cold-start prototype, not oversights — the
structural fixes are the production roadmap in the README.

---

## 1. The taxonomy gap (the main one) — category matching is label-keyed

Both the parser and the publisher matcher key on a **fixed category vocabulary** derived
from the catalog (`src/taxonomy.py`). The parser is allowed to mint a label that fits the
business better than any catalog category, and the matcher's CATEGORY FLOOR only fires on
an exact top-level `category` match. That one design choice bites in **both directions**:

**a) Under-reach — "15-minute grocery delivery" → *no match*.**
The parser labels the business something like `quick_commerce` (accurate, but not a
catalog category). No publisher's `category` string matches, so the floor fires for
nobody, and the matcher honestly-but-wrongly concludes "no strong match" — even though
**Swiftcart** (`instant_delivery`, with `groceries`/`convenience` subcategories) is a
near-perfect fit. The persona side matches fine (95), because personas carry
`quick_commerce` as an *affinity* string — different vocabulary, so no mismatch. The
divergence between the two matchers is the tell.

**b) Over-reach — "$400 premium luggage" → confident *apparel* campaign.**
Luggage has no catalog category, so the parser maps it to `apparel`. Now the floor *does*
fire, and audience-overlap publishers (premium clothing/shoes) get scored as "direct
category matches" with a full campaign and the apparel CVR — when the honest label is
"audience-adjacent, no true category publisher exists."

**Why not patched:** a prompt-level fix (subcategory-aware / semantic matching) was
prototyped and reverted — it added noise (broad subcategories bleed into many advertisers)
and risked regressing the 15 validated examples, which can't be cheaply re-verified.
**The real fix is structural:** a shared, normalized taxonomy that *both* the parser and
the matcher map into (so `quick_commerce` ≡ `instant_delivery`), and/or **embedding
recall** — match advertiser text against publisher category+subcategory text in vector
space, where "grocery delivery" and "instant delivery" are close by construction, no
string match needed. This is exactly the `embedding recall → LLM rerank` roadmap in the
README; this bug is its concrete motivation.

## 2. LLM non-determinism (`gpt-oss-20b`, temp 0.4)

Run-to-run variance is real: the parser sometimes labels the same business differently
(`instant_delivery` vs `quick_commerce`), and that difference cascades into persona
scoring. The matching rubric + post-filters keep it mostly stable, but ordering wobbles
a few points between runs. Mitigations: lower the parse temperature / constrain the
category to the taxonomy for stability now; the learned ranker removes the variance
entirely once there's conversion data.

## 3. Latency (~30–90s per run)

`gpt-oss-20b` is a reasoning model — it generates internal reasoning before the JSON,
which is most of the wall-clock time (and the reason the reasons are good). It's a
one-line `.env` swap to `GROQ_MODEL=llama-3.3-70b-versatile` for a large speedup at a
small quality cost. Structural wins: run publisher + persona matching concurrently and
batch the per-persona creative calls.

---

## Addressed during testing

- **Empty creative body.** When the claim-guard stripped a body whose only sentence
  carried an unsupported claim, it left a bare `"."`. Now it falls back to a grounded
  line built from the advertiser's own USP — never empty. (`src/creative_generator.py`)
- **Padded / non-match personas.** The selector used to force `MIN_PERSONAS=3` even when
  the LLM returned only one real match (surfacing score-0 personas with creatives). A
  `PERSONA_SELECT_FLOOR` now means a non-match is never shown or given a creative, even
  if that leaves fewer than three. (`src/config.py`, `matching._select`,
  `persona_matcher.match_personas`)
