"""Run the DATA-FREE parser on every example advertiser and save the results.

Reads data/example_advertisers.txt (the numbered one-liners), parses each with
experiments/data_free_parser.parse_advertiser_datafree (NO LLM), prints a readable
summary, and writes two files for inspection:
  * experiments/datafree_results.txt   (human-readable)
  * experiments/datafree_results.json  (structured, the full profile per example)

Run from the repo root:   python -m experiments.run_datafree_on_examples
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from experiments import data_free_parser  # read _EMBED_OK live; a from-import copies it at import time
from experiments.data_free_parser import parse_advertiser_datafree

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "example_advertisers.txt"
OUT_TXT = ROOT / "experiments" / "datafree_results.txt"
OUT_JSON = ROOT / "experiments" / "datafree_results.json"

# lines like "1. We sell premium dog food ..."
_NUM = re.compile(r"^\s*(\d+)\.\s+(.*)")


def load_examples() -> list[tuple[int, str]]:
    out = []
    for line in SRC.read_text(encoding="utf-8").splitlines():
        m = _NUM.match(line)
        if m:
            out.append((int(m.group(1)), m.group(2).strip()))
    return out


def main() -> None:
    examples = load_examples()
    # warm the model once so the per-example timings are fair
    parse_advertiser_datafree("warm up")
    engine = "embeddings" if data_free_parser._EMBED_OK else "lexical fallback (embedding model offline)"

    lines = [f"DATA-FREE PARSER — {len(examples)} examples   [category engine: {engine}]", "=" * 70]
    records = []
    for n, text in examples:
        t0 = time.perf_counter()
        p = parse_advertiser_datafree(text)
        dt = (time.perf_counter() - t0) * 1000
        block = (
            f"\n#{n}  ({dt:.2f} ms)\n  {text}\n"
            f"  category        : {p.product_category}\n"
            f"  subcategories   : {p.subcategories}\n"
            f"  positioning     : {p.price_positioning.value}   price_usd: {p.price_point_usd}\n"
            f"  expected_aov_usd: {p.expected_aov_usd}   seasonality: {p.seasonality}\n"
            f"  gender          : {getattr(p.target_gender, 'value', None)}   age: {p.target_age_range}\n"
            f"  geography       : {p.target_geography}\n"
            f"  business_model  : {getattr(p.business_model, 'value', None)}\n"
            f"  values          : {p.values}   brand_tone: {p.brand_tone}\n"
            f"  confidence      : {p.confidence}   (gate asks if < 0.45)\n"
        )
        lines.append(block)
        records.append({"n": n, "text": text, "ms": round(dt, 2),
                        "profile": json.loads(p.model_dump_json())})

    report = "\n".join(lines)
    OUT_TXT.write_text(report, encoding="utf-8")
    OUT_JSON.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(report)
    print(f"\nSaved -> {OUT_TXT}\nSaved -> {OUT_JSON}")
    gated = sum(1 for r in records if r["profile"]["confidence"] < 0.45)
    print(f"\n{len(examples)} parsed · {gated} would be gated (low confidence) · engine: {engine}")


if __name__ == "__main__":
    main()
