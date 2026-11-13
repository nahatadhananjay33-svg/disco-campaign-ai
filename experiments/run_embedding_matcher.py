"""Compare the EmbeddingMatcher (experiments) against the DeterministicMatcher (src)
on a few advertisers, and save the result. NO LLM, NO changes to src/.

On your laptop the EmbeddingMatcher uses real embeddings; offline it uses a lexical
fallback. The DeterministicMatcher is the rule-based baseline shipped in src/.

Run from the repo root:  python -m experiments.run_embedding_matcher
"""
from __future__ import annotations

import time
from pathlib import Path

from src.matching import get_matcher
from src.models import AdvertiserProfile, PricePositioning
from experiments.data_free_parser import _EMBED_OK, parse_advertiser_datafree  # noqa: F401
from experiments.embedding_matcher import EmbeddingMatcher, _sims

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "embedding_matcher_results.txt"

# A few clear advertisers (hand-built profiles so the matcher test is isolated from parsing).
CASES = {
    "premium dog food (pet, premium, subscription)": AdvertiserProfile(
        product_category="pet", subcategories=["pet_food", "dog"],
        price_positioning=PricePositioning.premium, values=[], confidence=0.9),
    "luxury leather handbags (apparel, luxury)": AdvertiserProfile(
        product_category="apparel", subcategories=["handbags", "leather"],
        price_positioning=PricePositioning.luxury, values=[], confidence=0.9),
    "sustainable activewear for women (apparel)": AdvertiserProfile(
        product_category="apparel", subcategories=["activewear"],
        price_positioning=PricePositioning.mid_premium, values=["sustainable"],
        target_audience=["women"], confidence=0.9),
}


def _top(matches, k=3):
    rec = [m for m in matches if not getattr(m, "excluded", False)]
    return rec[:k]


def main() -> None:
    import experiments.data_free_parser as dfp
    emb = EmbeddingMatcher()
    det = get_matcher("deterministic")
    # warm the embedding model / detect engine
    emb.rank_publishers(next(iter(CASES.values())))
    # ask the matcher which path it took; dfp._EMBED_OK is only set by the parser's classifier
    engine = "embeddings" if _sims("x", ["y"])[1] == "embedding" else "lexical fallback (model offline)"

    lines = [f"EMBEDDING MATCHER vs DETERMINISTIC MATCHER   [engine: {engine}]", "=" * 68]
    for label, profile in CASES.items():
        t0 = time.perf_counter()
        e_pubs = emb.rank_publishers(profile)
        e_pers = emb.rank_personas(profile)
        e_ms = (time.perf_counter() - t0) * 1000
        d_pubs = det.rank_publishers(profile)
        d_pers = det.rank_personas(profile)

        lines.append(f"\n### {label}   (embedding matcher: {e_ms:.2f} ms)")
        lines.append("  PUBLISHERS")
        lines.append("    embedding : " + ", ".join(f"{m.publisher_name}({m.score:.0f})" for m in _top(e_pubs)))
        lines.append("    rule-based: " + ", ".join(f"{m.publisher_name}({m.score:.0f})" for m in _top(d_pubs)))
        lines.append("  PERSONAS (selected)")
        lines.append("    embedding : " + ", ".join(m.persona_name for m in e_pers if m.selected))
        lines.append("    rule-based: " + ", ".join(m.persona_name for m in d_pers if m.selected))

    report = "\n".join(lines)
    OUT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved -> {OUT}")


if __name__ == "__main__":
    main()
