"""Vocabulary derived from the live catalog (publishers + personas).

Level-1 production move: the extraction prompt is driven by the data, not a
hardcoded list. Add a publisher or persona and the vocabulary — and therefore the
prompt — updates itself, with no prompt edit.

We inject ONLY vocabulary that helps extract the 16 fields and align them to what
we match on: categories (publishers), subcategories (publishers), geographies
(publishers), and the catalog's AOV range. Persona `messaging_preferences` and
`disinterested_in` are deliberately NOT injected — they belong to the creative
stage and the matching veto respectively.

The data source is abstracted here: today `build_vocabulary()` reads JSON via
data_loader; in production it would read a taxonomy DB / service and nothing else
would change. That single seam is the production-readiness story.
"""

from __future__ import annotations

from functools import lru_cache

from src.data_loader import load_personas, load_publishers


def _uniq(seq) -> list[str]:
    return sorted({str(x) for x in seq if x})


@lru_cache(maxsize=1)
def build_vocabulary() -> dict:
    pubs = load_publishers()
    pers = load_personas()

    aovs = [p["avg_order_value_usd"] for p in pubs if p.get("avg_order_value_usd")]
    aovs += [p["typical_aov_usd"] for p in pers if p.get("typical_aov_usd")]

    return {
        # Preferred-but-not-forced: the categories we actually have publishers for.
        "categories": _uniq(p["category"] for p in pubs),
        # Preferred vocabulary (the LLM may add others when they fit better).
        "subcategory_vocab": _uniq(s for p in pubs for s in p.get("subcategories", [])),
        "geo_labels": _uniq(g for p in pubs for g in p["audience"].get("top_geos", [])),
        "aov_low": int(min(aovs)) if aovs else 0,
        "aov_high": int(max(aovs)) if aovs else 0,
    }
