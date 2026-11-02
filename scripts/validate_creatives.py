"""Step 3 — generate one creative per selected persona, and SAVE for analysis.

Reuses the personas already selected in docs/step2_matching_results.json (so it only
makes creative calls, no re-parse/re-match). For each example and each selected
persona it generates a creative and records the persona's messaging_preferences +
disinterested_in alongside, so you can check: does the copy fit the persona, avoid
their dislikes, match the price register, and stay grounded in the advertiser's facts?

Writes:
    docs/step3_creatives.md    (readable, per example/persona)
    docs/step3_creatives.json  (structured)

Run from the project root (needs GROQ_API_KEY in .env):
    python -u scripts/validate_creatives.py            # all examples in the step2 file
    python -u scripts/validate_creatives.py 1 10 13    # specific ones
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.creative_generator import generate_creative
from src.data_loader import load_personas
from src.derivation import target_sensitivity_for
from src.llm import call_json
from src.models import AdvertiserProfile

STEP2 = Path("docs/step2_matching_results.json")
OUT_MD = Path("docs/step3_creatives.md")
OUT_JSON = Path("docs/step3_creatives.json")


def log(*a):
    print(*a, flush=True)


def main():
    if not STEP2.exists():
        log(f"ERROR: {STEP2} not found — run validate_matching.py first.")
        return
    data = json.load(open(STEP2, encoding="utf-8"))
    personas_by_id = {p["id"]: p for p in load_personas()}

    args = sys.argv[1:]
    keys = [a for a in args if a in data] or sorted(data, key=int)

    results: dict[str, dict] = {}
    md: list[str] = ["# Step 3 — persona-tuned creatives\n"]

    for k in keys:
        e = data[k]
        prof = AdvertiserProfile.model_validate(e["profile"])
        if prof.product_category is None:          # gated/off-catalog example, no creatives
            continue
        selected = [p for p in e["personas"] if p.get("selected")]
        pos = prof.price_positioning.value
        log("\n" + "=" * 92)
        log(f"#{k}  {e['input'][:70]}")
        log(f"  positioning={pos} target_sens={target_sensitivity_for(pos)} seasonality={prof.seasonality}")

        md.append(f"\n## #{k} — {e['input'][:70]}")
        md.append(f"*positioning `{pos}` · target_sensitivity `{target_sensitivity_for(pos)}` · "
                  f"seasonality `{prof.seasonality}` · values: {', '.join(prof.values) or '—'}*\n")

        rows = []
        for sp in selected:
            persona = personas_by_id.get(sp["id"])
            if not persona:
                continue
            c = generate_creative(prof, persona, llm_call=call_json)
            rows.append({"persona": persona["name"], "score": sp["score"],
                         "price_sensitivity": persona.get("price_sensitivity"),
                         "messaging_preferences": persona.get("messaging_preferences"),
                         "disinterested_in": persona.get("disinterested_in"),
                         "headline": c.headline, "body": c.body,
                         "angle": c.messaging_angle, "reasoning": c.reasoning})
            log(f"  [{persona['name']}] {c.headline} | {c.body}")
            md.append(f"**{persona['name']}**  (score {sp['score']:.0f} · "
                      f"price_sens `{persona.get('price_sensitivity')}`)")
            md.append(f"- prefs: {', '.join(persona.get('messaging_preferences', []))}")
            md.append(f"- avoids: {', '.join(persona.get('disinterested_in', []))}")
            md.append(f"- **{c.headline}** — {c.body}")
            md.append(f"- angle: {c.messaging_angle} · why: {c.reasoning}\n")
        results[k] = {"input": e["input"], "positioning": pos, "creatives": rows}

    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    log(f"\nSAVED -> {OUT_MD}  and  {OUT_JSON}")


if __name__ == "__main__":
    main()
