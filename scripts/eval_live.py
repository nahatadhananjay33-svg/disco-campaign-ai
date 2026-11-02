"""Live evaluation of the REAL Gemini pipeline over the synthetic dataset.

Unlike the offline tests, this calls Gemini for real, so it checks what the
tests can't: does the LLM parser assign the right confidence (gate vague inputs,
accept clear ones) and extract a sensible category? Prints a table for manual
review and an automatic pass/fail on the confidence gate.

Usage (from the project root, venv active, GEMINI_API_KEY set in .env):
    python scripts/eval_live.py                 # parser + matching only (~35 calls, fast)
    python scripts/eval_live.py --with-creatives # also generate creatives (many more calls)
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from src.data_loader import load_publishers  # noqa: E402
from src.llm import LLMError  # noqa: E402
from src.pipeline import run_pipeline  # noqa: E402

DATASET = json.loads((ROOT / "data" / "synthetic_advertisers.json").read_text())
PUB_CAT = {p["id"]: p["category"] for p in load_publishers()}


def _creative_stub(prompt):  # used unless --with-creatives
    return {"headline": "x", "body": "x", "messaging_angle": "x", "reasoning": "x"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-creatives", action="store_true",
                    help="also call the LLM to generate creatives (uses many more calls)")
    args = ap.parse_args()
    creative_llm = None if args.with_creatives else _creative_stub

    passed = failed = 0
    print(f"{'id':4} {'kind':11} {'conf':>5} {'gated':5} {'result':7} top publishers")
    print("-" * 90)

    for case in DATASET:
        kwargs = {} if creative_llm is None else {"creative_llm": creative_llm}
        try:
            r = run_pipeline(case["text"], **kwargs)
        except LLMError as exc:
            print(f"{case['id']:4} {case['kind']:11}  ERROR  {str(exc)[:60]}")
            failed += 1
            continue

        gated = r.needs_clarification
        conf = r.profile.confidence

        # Automatic check: does the gate match the expectation?
        if case["kind"] == "ambiguous":
            ok = gated
        elif case["kind"] in ("clear", "off_catalog"):
            ok = not gated
        else:
            ok = True
        verdict = "PASS" if ok else "FAIL"
        passed += ok
        failed += (not ok)

        tops = ""
        if not gated:
            rec = [m for m in r.publishers if not m.excluded][:3]
            tops = ", ".join(f"{m.publisher_name}({PUB_CAT[m.publisher_id]})" for m in rec) or "(none)"
        print(f"{case['id']:4} {case['kind']:11} {conf:5.2f} {str(gated):5} {verdict:7} {tops}")

    print("-" * 90)
    print(f"Gate check: {passed} passed / {failed} failed (out of {len(DATASET)}).")
    print("Now eyeball the 'clear' rows: the top publisher's category (in parens) "
          "should match the business. 'off_catalog' rows should show weak/no fits.")


if __name__ == "__main__":
    main()
