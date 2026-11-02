"""Step 4 — build the full campaign.json for every example from the saved Step 2
matches and Step 3 creatives (deterministic; no LLM), and render EVERY field with
its value AND the reasoning for that value. Saves docs/step4_campaigns.{md,json}.

Run from the project root:  python scripts/validate_campaigns.py
(Set STEP_SRC to read the saved json from elsewhere.)
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import AdvertiserProfile, PublisherMatch, PersonaMatch, FactorScore, Creative
from src.campaign_builder import build_campaign

SRC = Path(os.environ.get("STEP_SRC", "docs"))
OUT = Path("docs")
s2 = json.load(open(SRC / "step2_matching_results.json"))
s3 = json.load(open(SRC / "step3_creatives.json"))
N2ID = {p["name"]: p["id"] for p in json.load(open("data/shopper_personas.json"))}
PBYID = {p["id"]: p for p in json.load(open("data/shopper_personas.json"))}


def one(k):
    e = s2[k]
    prof = AdvertiserProfile.model_validate(e["profile"])
    pubs = [PublisherMatch(publisher_id=p["id"], publisher_name=p["name"], score=p["score"],
            factors=[FactorScore(name="x", raw=min(p["score"], 100), weight=1.0)],
            reason=p["reason"], excluded=p["excluded"]) for p in e["publishers"]]
    sel = [PersonaMatch(persona_id=p["id"], persona_name=p["name"], score=p["score"],
           factors=[FactorScore(name="x", raw=min(p["score"], 100), weight=1.0)],
           reason=p["reason"], selected=True) for p in e["personas"] if p["selected"]]
    crs = [Creative(persona_id=N2ID.get(c["persona"], "?"), persona_name=c["persona"],
           headline=c["headline"], body=c["body"], messaging_angle=c["angle"],
           reasoning=c["reasoning"]) for c in s3.get(k, {}).get("creatives", [])]
    return prof, build_campaign(prof, pubs, sel, PBYID, creatives=crs)


def tbl(rows):
    out = ["| Field | Value | Why this value |", "|--|--|--|"]
    out += [f"| `{f}` | {v} | {w} |" for f, v, w in rows]
    return "\n".join(out)


def render(k, prof, c):
    b, f, m, fb = c.bid_strategy, c.forecast, c.measurement, c.feedback
    cpc = f"${b.suggested_cpc_range_usd[0]:.2f}–{b.suggested_cpc_range_usd[1]:.2f}"
    aov_note = next((a for a in c.assumptions if a.startswith("Target CPA")), "")
    md = [f"\n## #{k} — {s2[k]['input']}\n"]

    md.append("### Identity & lifecycle")
    md.append(tbl([
        ("campaign_id", f"`{c.campaign_id}`", "unique id so logged results can be joined back to this plan"),
        ("created_at", f"`{c.created_at}`", "when the plan was generated (audit trail)"),
        ("status", f"`{c.status}`", "a plan, not live — needs human approval before launch"),
    ]))

    md.append("\n### Objective & category")
    md.append(tbl([
        ("objective", f"`{c.objective}`", "conversions for DTC / lead_generation for B2B — what the system optimizes toward"),
        ("advertiser_category", f"`{c.advertiser_category}`", "the vertical; drives the CVR benchmark and reporting"),
    ]))

    md.append("\n### Targeting — *who* sees the ad")
    md.append(tbl([
        ("personas", ", ".join(c.targeting.personas), "matched shopper segments; each gets its own creative"),
        ("interests", ", ".join(c.targeting.interests), "interest keywords (from subcats + USP) to target on"),
        ("geographies", ", ".join(c.targeting.geographies), "the recommended publishers' top geos; don't serve where unfulfillable"),
        ("age_range", c.targeting.age_range, "the advertiser's intended age (distinct from a publisher's audience skew)"),
        ("gender", c.targeting.gender, "the advertiser's intended gender; avoids wasted impressions on gendered products"),
    ]))

    md.append("\n### Publishers — *where* (budget split ∝ match score)")
    md.append("| Publisher | Budget % | Why |\n|--|--|--|")
    for a in c.publishers:
        md.append(f"| {a.publisher_name} | {a.budget_percentage}% | share proportional to its Step-2 match score |")

    md.append("\n### Budget — *how much*")
    md.append(tbl([
        ("daily_budget", f"${c.budget.daily_budget:.0f}", f"{f.target_conversions_per_day} target conversions/day × ${b.target_cpa_usd:.0f} CPA"),
        ("total_budget", f"${c.budget.total_budget:.0f}", f"daily × {c.budget.flight_days}-day flight (lifetime cap)"),
        ("flight_days", c.budget.flight_days, "assumed campaign length"),
        ("pacing", f"`{c.budget.pacing}`", "spend the daily budget evenly through the day"),
        ("basis", f"`{c.budget.basis}`", "flags that we set this — the advertiser gave no budget"),
    ]))

    md.append("\n### Bid strategy — *how* to buy")
    md.append(tbl([
        ("target_cpa_usd", f"${b.target_cpa_usd:.0f}", aov_note.replace("Target CPA ", "").rstrip(".")),
        ("suggested_cpc_range_usd", cpc, f"CPA × CVR (${b.target_cpa_usd:.0f} × {f.estimated_cvr*100:.1f}%), ±20%"),
        ("aggressiveness", f"`{b.aggressiveness}`", "from the audience's price-sensitivity — low-sensitivity → bid up"),
    ]))

    md.append("\n### Forecast — *what the spend buys*")
    md.append(tbl([
        ("estimated_cvr", f"{f.estimated_cvr*100:.1f}%", f.cvr_basis.split("— ", 1)[-1].split(". 2024")[0]),
        ("target_conversions_per_day", f.target_conversions_per_day, "the volume the budget is sized for"),
        ("estimated_clicks_per_day", f"{f.estimated_clicks_per_day:,}", "daily budget ÷ CPC"),
        ("estimated_impressions_per_day", f"{f.estimated_impressions_per_day:,}", "clicks ÷ assumed 0.8% display CTR"),
        ("available_monthly_impressions", f"{f.available_monthly_impressions:,}", "inventory pool across recommended publishers — can the audience absorb the spend?"),
        ("expected_roas", f"{f.expected_roas}x", "AOV ÷ CPA — revenue per ad dollar"),
    ]))

    md.append("\n### Measurement — *how success is defined*")
    md.append(tbl([
        ("conversion_event", f"`{m.conversion_event}`", "what counts as a conversion"),
        ("attribution_window_days", m.attribution_window_days, "how long after a click a conversion still counts"),
        ("optimization_goal", f"`{m.optimization_goal}`", "what the system tunes toward"),
        ("kpi_targets", f"CPA ${m.kpi_targets.target_cpa_usd:.0f} / ROAS {m.kpi_targets.target_roas}x", "the bar the campaign is judged against"),
    ]))

    md.append("\n### Feedback — *predicted vs actual (training data)*")
    md.append(tbl([
        ("predicted", f"cvr {fb.predicted.cvr*100:.1f}%, cpa ${fb.predicted.cpa_usd:.0f}, {fb.predicted.conversions_per_day:.0f}/day, roas {fb.predicted.roas}x", "what this plan forecasts"),
        ("actual", "null", "filled post-launch — the predicted-vs-actual gap is the training label for a learned ranker"),
    ]))

    md.append("\n### Creatives — *what it says* (one per persona)")
    md.append("| Persona | Headline |\n|--|--|")
    for cr in c.creatives:
        md.append(f"| {cr.persona_name} | {cr.headline} |")
    return "\n".join(md)


out, md = {}, ["# Step 4 — full campaign.json per example, every field with reasoning\n"]
for k in sorted(s2, key=int):
    if s2[k]["profile"].get("product_category") is None:
        continue
    prof, c = one(k)
    out[k] = c.model_dump()
    md.append(render(k, prof, c))

json.dump(out, open(OUT / "step4_campaigns.json", "w"), indent=2, default=str)
open(OUT / "step4_campaigns.md", "w").write("\n".join(md) + "\n")
print("wrote", len(out), "campaigns")
