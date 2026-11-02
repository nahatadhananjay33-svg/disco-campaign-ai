"""Demonstrate the LLM fallbacks: block different LLM calls and show that every
stage (Step 1 parse -> 2 match -> 3 creative -> 4 campaign) still returns a valid
result. No real API needed — stubs raise LLMError to simulate "the LLM is down".

Run from the project root:  python scripts/demo_fallbacks.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import load_personas
from src.llm import LLMError
from src.pipeline import run_pipeline

PERS = {p["id"]: p for p in load_personas()}
PET = {"product_category": "pet", "subcategories": ["pet_food", "grain_free", "subscription"],
       "target_gender": "all", "target_age_range": "30-55", "price_positioning": "premium",
       "brand_tone": ["trustworthy"], "values": ["vet-formulated", "grain-free"],
       "unique_selling_points": ["grain-free vet-formulated senior dog food"],
       "business_model": "subscription", "confidence": 0.9}
SOFT = {**PET, "product_category": "software", "subcategories": ["saas", "dental_software"],
        "business_model": "b2b", "unique_selling_points": ["automates dental patient recall"],
        "values": ["efficiency"], "price_positioning": "unknown"}


def down(_):
    raise LLMError("BLOCKED")


def creative_ok(_):
    return {"headline": "Grain-free senior dog nutrition", "body": "Vet-formulated, delivered monthly.",
            "messaging_angle": "health", "reasoning": "stubbed LLM creative"}


def make_match(cat, block_pub=False, block_all=False):
    """A stub LLM matcher that can selectively 'go down' for publisher/persona calls."""
    def match(prompt):
        if block_all:
            raise LLMError("BLOCKED")
        if 'Return ONLY JSON: {"note"' in prompt:                       # explain_gap call
            return {"note": f"No catalog publisher serves this advertiser; ideal = a dedicated {cat} channel."}
        if "avg_order_value" in prompt:                                 # publisher call
            if block_pub:
                raise LLMError("BLOCKED")
            ids = re.findall(r'"id": "(pub_\d+)"', prompt); cats = re.findall(r'"category": "([^"]+)"', prompt)
            return {"matches": [{"id": i, "score": (92 if c == cat else 15), "reason": "stub"} for i, c in zip(ids, cats)]}
        ids = re.findall(r'"id": "(persona_\d+)"', prompt)              # persona call
        return {"matches": [{"id": i, "score": (90 if any(cat in a for a in PERS.get(i, {}).get("category_affinities", [])) else 20),
                             "reason": "stub"} for i in ids]}
    return match


SCENARIOS = [
    ("1. ALL LLM HEALTHY (pet)",            "pet text",     lambda _: dict(PET),  make_match("pet"),                 creative_ok),
    ("2. STEP-1 PARSE DOWN (apparel text)", "Premium apparel activewear for women, $80", down, make_match("apparel"), creative_ok),
    ("3. STEP-2 PUBLISHER LLM DOWN (pet)",  "pet text",     lambda _: dict(PET),  make_match("pet", block_pub=True), creative_ok),
    ("4. STEP-2 BOTH MATCHERS DOWN (pet)",  "pet text",     lambda _: dict(PET),  make_match("pet", block_all=True), creative_ok),
    ("5. STEP-3 CREATIVE LLM DOWN (pet)",   "pet text",     lambda _: dict(PET),  make_match("pet"),                 down),
    ("6. OFF-CATALOG -> coverage none (b2b)", "b2b text",   lambda _: dict(SOFT), make_match("software"),            creative_ok),
]

for name, text, pstub, mstub, cstub in SCENARIOS:
    r = run_pipeline(text, parse_llm=pstub, match_llm=mstub, creative_llm=cstub, matcher="llm")
    print("=" * 92); print(name)
    print("  fallbacks fired:", r.degraded_notes or ["(none — all LLM healthy)"])
    p = r.profile
    print(f"  STEP1: cat={p.product_category} positioning={p.price_positioning.value} "
          f"price={p.price_point_usd} conf={p.confidence}")
    if r.needs_clarification:
        print("  -> GATED (too vague): clarifying questions, no campaign."); continue
    rec = [m for m in r.publishers if not m.excluded][:3]
    print(f"  STEP2: pubs={[(m.publisher_name, round(m.score)) for m in rec] or 'NONE (all excluded)'}")
    print(f"         personas={[m.persona_name for m in r.personas if m.selected]}")
    if r.coverage == "none":
        print(f"  COVERAGE=NONE -> no creatives, no campaign. note: {r.coverage_note[:70]}"); continue
    print(f"  STEP3: creatives={[c.headline for c in r.creatives]}")
    if any(c.reasoning.startswith("Template") for c in r.creatives):
        print("         (template fallback used)")
    if r.campaign:
        print(f"  STEP4: CPA=${r.campaign.bid_strategy.target_cpa_usd:.0f} "
              f"budget=${r.campaign.budget.daily_budget:.0f}/day CVR={r.campaign.forecast.estimated_cvr*100:.1f}%")
