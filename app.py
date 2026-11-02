"""Streamlit UI — the thin 'click through it and see it work' layer the brief asks
for. All logic lives in src/; this file only renders a CampaignResult.

Run: streamlit run app.py
"""

import json
import os
import time

from dotenv import load_dotenv
import streamlit as st

from src.data_loader import load_personas
from src.llm import LLMError
from src.models import CampaignResult
from src.pipeline import run_pipeline

load_dotenv()

st.set_page_config(page_title="Disco Campaign AI", page_icon="📣", layout="wide")

# Raw persona catalog, keyed by id — lets the creative view show the exact fields
# (affinities, messaging preferences, disinterests) the copy was tuned against.
_PERSONAS_BY_ID = {p["id"]: p for p in load_personas()}


# --- small render helpers ---------------------------------------------------

def _humanize(items, n=None):
    """'pet_food', 'subscription_boxes' -> 'pet food, subscription boxes'."""
    vals = [str(x).replace("_", " ") for x in (items or [])]
    if n:
        vals = vals[:n]
    return ", ".join(vals)


def _md_safe(text) -> str:
    """Escape '$' in LLM-generated text so Streamlit doesn't read a '$...$' span as
    LaTeX math — which otherwise mangles dollar amounts (e.g. '$78 ... $1,200') into
    broken vertical text."""
    return str(text).replace("$", "\\$")


def _render_publishers(result: CampaignResult):
    recommended = [m for m in result.publishers if not m.excluded]
    excluded = [m for m in result.publishers if m.excluded]

    st.subheader("Recommended publishers")
    # Same clean shape as personas: name + score inline, the LLM's reason right
    # underneath. (No "why this score" expander — for the LLM matcher it only
    # repeated the single score, which read as noise.)
    for m in recommended[:5]:
        with st.container(border=True):
            st.markdown(f"**{m.publisher_name}** · score {m.score:.0f}")
            st.caption(_md_safe(m.reason))

    if excluded:
        with st.expander(f"Excluded publishers ({len(excluded)}) — and why"):
            for m in excluded:
                st.markdown(f"**{m.publisher_name}** ({m.score:.0f}) — {_md_safe(m.reason)}")


def _render_personas(result: CampaignResult):
    st.subheader("Shopper personas")
    for m in [p for p in result.personas if p.selected]:
        badge = " ⚠️ demoted (disinterest conflict)" if m.disinterest_conflict else ""
        with st.container(border=True):
            st.markdown(f"**{m.persona_name}** · score {m.score:.0f}{badge}")
            st.caption(_md_safe(m.reason))


def _render_creatives(result: CampaignResult):
    """Each creative with its reasoning made fully visible (as the brief asks):
    the persona's real signals, the ad itself, then a field-by-field read of WHY
    the copy lands — hook, voice, register, what it avoids, what grounds it."""
    st.subheader(f"Ad creatives ({len(result.creatives)} variants)")

    scores = {m.persona_id: m.score for m in result.personas}
    prof = result.profile
    tone = _humanize(prof.brand_tone) or "the brand's tone"
    usps = "; ".join(prof.unique_selling_points) or (prof.product_category or "the product")
    pos = prof.price_positioning.value

    for c in result.creatives:
        persona = _PERSONAS_BY_ID.get(c.persona_id, {})
        aff = persona.get("category_affinities", [])
        prefs = persona.get("messaging_preferences", [])
        avoids = persona.get("disinterested_in", [])
        psens = persona.get("price_sensitivity", "")
        score = scores.get(c.persona_id)

        with st.container(border=True):
            head = f"**{c.persona_name}**"
            if score is not None:
                head += f" · match {score:.0f}"
            if psens:
                head += f" · price-sens `{psens}`"
            st.markdown(head)

            # the persona's real signals the copy was written against
            sig = []
            if aff:
                sig.append("affinities " + _humanize(aff, 4))
            if prefs:
                sig.append("responds to " + _humanize(prefs, 3))
            if avoids:
                sig.append("avoids " + _humanize(avoids, 3))
            if sig:
                st.caption(" · ".join(sig))

            # the ad itself
            st.markdown(f"### {_md_safe(c.headline)}")
            st.write(_md_safe(c.body))

            # the visible, field-by-field reasoning
            st.markdown("**Why it reads this way**")
            bullets = []
            if aff:
                bullets.append(f"**Hook** — opens on the persona's interest in *{_humanize(aff, 2)}* "
                               f"(angle: {_md_safe(c.messaging_angle)}).")
            bullets.append(f"**Voice** — the persona's preferred style ({_humanize(prefs) or '—'}) "
                           f"carried in the brand's tone ({tone}).")
            bullets.append(f"**Register** — matched to the `{pos}` price positioning.")
            if avoids:
                bullets.append(f"**Avoided** — steers clear of {_humanize(avoids, 3)}.")
            bullets.append(f"**Grounded in** — {_md_safe(usps)} (no invented claims).")
            if c.reasoning:
                bullets.append(f"**Model's own reasoning** — {_md_safe(c.reasoning)}")
            for b in bullets:
                st.markdown("- " + b)


def _render_campaign(result: CampaignResult):
    st.subheader("Campaign config")
    cfg = result.campaign.model_dump()
    st.json(cfg)
    st.download_button(
        "Download campaign.json",
        data=json.dumps(cfg, indent=2, default=str),
        file_name="campaign.json",
        mime="application/json",
    )
    if result.campaign.assumptions:
        with st.expander("Assumptions the system made"):
            for a in result.campaign.assumptions:
                st.markdown(f"- {a}")


# --- page -------------------------------------------------------------------

st.title("📣 Disco Campaign AI")
st.caption(
    "Describe a business in a sentence or two. The system drafts a campaign: "
    "where to advertise, who to speak to, and what to say."
)

with st.sidebar:
    st.header("Setup")
    if os.getenv("GROQ_API_KEY"):
        st.success("Groq key detected.")
    else:
        st.error("No GROQ_API_KEY. Add it to .env to generate.")
        st.caption("Free key: console.groq.com/keys")
    st.divider()
    st.caption(
        "LLM (Groq): advertiser understanding, publisher & persona matching, creative.\n\n"
        "Deterministic Python: campaign config. Matching scales via embedding "
        "recall → LLM rerank (see README)."
    )

# Manual entry is the whole point of the demo — type a business, generate.
description = st.text_area(
    "Advertiser description",
    placeholder="e.g. Premium grain-free dog food for senior dogs, subscription-based, about $60/box",
    height=100,
)

if st.button("Generate campaign", type="primary", disabled=not description.strip()):
    try:
        t0 = time.time()
        with st.spinner("Thinking…"):
            result = run_pipeline(description)
        elapsed = time.time() - t0
    except LLMError as exc:
        st.error(f"LLM error: {exc}")
        st.stop()

    st.caption(f"⚡ Generated in {elapsed:.1f}s")

    conf = result.profile.confidence
    st.progress(conf, text=f"Understanding confidence: {conf:.0%}")

    if result.needs_clarification:
        st.warning("This description is too vague to build a reliable campaign. A few questions:")
        for q in result.profile.clarifying_questions:
            st.markdown(f"- {q}")
        if result.profile.missing_information:
            st.caption("Missing: " + ", ".join(result.profile.missing_information))
        st.stop()

    for note in result.degraded_notes:
        st.info("⚙️ " + note)

    with st.expander("Extracted advertiser profile"):
        st.json(result.profile.model_dump())

    if result.coverage == "none":
        st.error("No strong match in the catalog for this advertiser — not forcing a campaign.")
        if result.coverage_note:
            st.caption(result.coverage_note)
        _render_publishers(result)   # best-available, all excluded — shown for transparency
        _render_personas(result)
        st.stop()

    if result.coverage == "weak":
        st.warning("Weak catalog coverage — showing the best available (low confidence).")
        if result.coverage_note:
            st.caption(result.coverage_note)

    _render_publishers(result)
    _render_personas(result)
    _render_creatives(result)
    if result.campaign:
        _render_campaign(result)
