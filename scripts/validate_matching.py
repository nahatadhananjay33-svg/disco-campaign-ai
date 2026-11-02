"""See Step 2 end-to-end AND save it for analysis.

For each advertiser: the extracted profile (incl. derived economics), the FULL
ranked publishers and personas (every item, with score + reason + excluded/selected
flags). For the first example it also records the exact JSON briefs fed to the LLM,
so you can confirm EVERY publisher/persona meta field is actually being sent.

Writes two files you can analyze:
    docs/step2_matching_results.md    (human-readable, per example)
    docs/step2_matching_results.json  (full structured scores)

Run from the project root (needs GROQ_API_KEY in .env):
    python -u scripts/validate_matching.py            # all 15 (skips ones already saved)
    python -u scripts/validate_matching.py 1 10 13     # specific ones (re-runs them)
Delete docs/step2_matching_results.json to start fresh.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.advertiser_parser import parse_advertiser
from src.derivation import price_range_for, target_sensitivity_for
from src.llm import call_json
from src.matching import _pub_brief, _per_brief, _profile_brief_for, PUB_PROFILE_FIELDS, get_matcher
from src.data_loader import load_publishers, load_personas

OUT_MD = Path("docs/step2_matching_results.md")
OUT_JSON = Path("docs/step2_matching_results.json")


def log(*a):
    print(*a, flush=True)


def _inputs():
    out = {}
    for ln in open("data/example_advertisers.txt", encoding="utf-8"):
        m = re.match(r"\s*(\d+)\.\s+(.*)", ln)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def main():
    args = [a for a in sys.argv[1:] if a != "all"]
    inputs = _inputs()
    keys = [a for a in args if a in inputs] or sorted(inputs, key=int)

    matcher = get_matcher("llm", llm_call=call_json)
    # Resume: keep examples already saved, and save after each one, so a rate-limit
    # crash loses nothing and a rerun continues where it stopped.
    results: dict[str, dict] = json.loads(OUT_JSON.read_text(encoding="utf-8")) if OUT_JSON.exists() else {}
    if not args:
        keys = [k for k in keys if k not in results]
    first = not any("_wiring_check" in r for r in results.values())

    for k in keys:
        desc = inputs[k]
        log("\n" + "=" * 96)
        log(f"#{k}  {desc}")
        prof = parse_advertiser(desc, llm_call=call_json)
        pos = prof.price_positioning.value
        prof_line = (f"cat={prof.product_category} | positioning={pos} | price={prof.price_point_usd} | "
                     f"expected_aov=${prof.expected_aov_usd} | range={price_range_for(pos)} | "
                     f"target_sens={target_sensitivity_for(pos)} | "
                     f"gender={prof.target_gender.value if prof.target_gender else None} | "
                     f"seasonality={prof.seasonality}")
        log("PROFILE: " + prof_line)

        pubs = matcher.rank_publishers(prof)
        pers = matcher.rank_personas(prof)

        pub_rows = [{"id": p.publisher_id, "name": p.publisher_name, "score": p.score,
                     "excluded": p.excluded, "reason": p.reason} for p in pubs]
        per_rows = [{"id": p.persona_id, "name": p.persona_name, "score": p.score,
                     "selected": p.selected, "reason": p.reason} for p in pers]
        results[k] = {"input": desc, "profile_line": prof_line, "profile": prof.model_dump(mode="json"),
                      "publishers": pub_rows, "personas": per_rows}
        if first:
            first = False
            results[k]["_wiring_check"] = {
                "advertiser_brief": _profile_brief_for(prof, PUB_PROFILE_FIELDS),
                "sample_publisher_brief": _pub_brief(load_publishers()[3]),
                "sample_persona_brief": _per_brief(load_personas()[4]),
            }

        log("  PUBLISHERS (recommended): " + ", ".join(f"{p.publisher_name} {p.score:.0f}" for p in pubs if not p.excluded))
        log("  PERSONAS (selected): " + ", ".join(f"{p.persona_name} {p.score:.0f}" for p in pers if p.selected))
        _save(results)
        log(f"  saved #{k} ({len(results)}/{len(inputs)} done)")

    _save(results)
    log(f"\nSAVED -> {OUT_MD}  and  {OUT_JSON}")


def _save(results: dict) -> None:
    md: list[str] = ["# Step 2 — matching results (every field wired)\n"]
    for k in sorted(results, key=int):
        r = results[k]
        md.append(f"\n## #{k} — {r['input']}\n")
        md.append(f"**Profile:** {r.get('profile_line', '')}\n")
        if "_wiring_check" in r:
            md.append("<details><summary>wiring check — exact briefs sent to the LLM</summary>\n")
            md.append("```json\n" + json.dumps(r["_wiring_check"], indent=2, default=str) + "\n```\n</details>\n")
        md.append("\n**Publishers (all, ranked):**\n")
        md.append("| score | publisher | excluded | reason |\n|--:|--|--|--|")
        for p in r["publishers"]:
            md.append(f"| {p['score']:.0f} | {p['name']} | {'yes' if p['excluded'] else ''} | {p['reason']} |")
        md.append("\n**Personas (all, ranked):**\n")
        md.append("| score | persona | selected | reason |\n|--:|--|--|--|")
        for p in r["personas"]:
            md.append(f"| {p['score']:.0f} | {p['name']} | {'yes' if p['selected'] else ''} | {p['reason']} |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
