"""EXPERIMENT (not part of src/) — EmbeddingMatcher v2: a THIRD matching strategy
behind src.matching.Matcher, with NO LLM and NO training data.

Beyond plain cosine argmax, it adds three data-free upgrades (the fix for the
over/under-selection we saw in v1):

  1. DISINTEREST / economics MULTIPLIER — cosine ignores a persona's `disinterested_in`;
     we multiply its score by 0.4 on a conflict (same idea as the deterministic matcher),
     so e.g. a fitness persona stops ranking for luxury handbags.
  2. SOFTMAX PROB-MASS selection — instead of a hard gap, softmax the scores and keep
     items until the cumulative probability passes a threshold -> a *calibrated* count
     (consistently 3-5), not "1 for one advertiser, 5 for another".
  3. MMR (Maximal Marginal Relevance) — pick a DIVERSE set (relevance minus redundancy),
     so we don't select three near-duplicate personas.

Still drop-in: subclasses Matcher, returns the same Pydantic objects, reuses the Step-1
embedding model. Offline it falls back to lexical similarity (no MMR there).
"""
from __future__ import annotations

import re

import numpy as np

from src.config import MIN_PERSONAS, TOP_PERSONAS
from src.data_loader import load_personas, load_publishers
from src.matching import Matcher
from src.models import AdvertiserProfile, FactorScore, PersonaMatch, PublisherMatch
from experiments.data_free_parser import _embed

_TOK = re.compile(r"[a-z0-9]+")

# tuning knobs (data-free; may need a small tweak once you see the embedding scores)
SOFTMAX_TEMP = 10.0
PROB_MASS = 0.70                 # select until cumulative softmax prob passes this
PUB_MIN, PUB_MAX = 3, 5          # recommend between this many publishers
DISINTEREST_MULT = 0.4          # score multiplier on a persona disinterest conflict
MMR_LAMBDA = 0.7                # relevance vs diversity (1 = pure relevance)
PERSONA_FLOOR_EMB, PERSONA_FLOOR_LEX = 0.22, 0.06   # absolute relevance floor


def _adv_text(p: AdvertiserProfile) -> str:
    parts = [p.product_category or ""] + p.subcategories + [p.price_positioning.value] \
        + p.values + p.brand_tone + p.target_audience
    return " ".join(x for x in parts if x)


def _pub_text(pub: dict) -> str:
    a = pub.get("audience", {})
    return " ".join(x for x in [pub["category"]] + pub.get("subcategories", [])
                    + [a.get("income_tier", ""), pub.get("notes", "")] if x)


def _per_text(per: dict) -> str:
    return " ".join(x for x in per.get("category_affinities", [])
                    + per.get("messaging_preferences", [])
                    + [per.get("price_sensitivity", ""), per.get("description", "")] if x)


def _score(adv_text: str, item_texts: list[str]):
    """Return (scores, item_matrix_or_None, method). Embeddings if available, else
    lexical Jaccard (no matrix -> MMR is skipped in that mode)."""
    try:
        adv = _embed([adv_text])[0]
        mat = _embed(item_texts)                 # (n, d), L2-normalized
        return mat @ adv, mat, "embedding"
    except Exception:
        at = set(_TOK.findall(adv_text.lower()))
        s = np.array([len(at & (t2 := set(_TOK.findall(t.lower())))) / max(1, len(at | t2))
                      for t in item_texts], dtype=np.float32)
        return s, None, "lexical"


def _sims(adv_text: str, item_texts: list[str]):
    """Back-compat shim (the runner uses this to report the engine)."""
    s, _, m = _score(adv_text, item_texts)
    return s, m


def _softmax(x: np.ndarray) -> np.ndarray:
    z = (x - x.max()) * SOFTMAX_TEMP
    e = np.exp(z)
    return e / e.sum()


def _count_by_mass(scores: np.ndarray, lo: int, hi: int) -> int:
    """How many to keep: add items (best first) until softmax prob-mass >= PROB_MASS."""
    p = _softmax(np.asarray(scores, dtype=np.float32))
    cum, k = 0.0, 0
    for idx in np.argsort(p)[::-1]:
        cum += p[idx]; k += 1
        if cum >= PROB_MASS:
            break
    return int(max(lo, min(hi, k)))


def _mmr(mat, scores: np.ndarray, eligible: list[int], k: int) -> list[int]:
    """Greedy MMR: relevance minus max similarity to what's already chosen (diversity)."""
    if mat is None:                               # lexical mode: no vectors -> top-k by score
        return sorted(eligible, key=lambda i: -scores[i])[:k]
    r = {i: float(scores[i]) for i in eligible}
    lo, hi = min(r.values()), max(r.values())
    rn = {i: (r[i] - lo) / (hi - lo + 1e-9) for i in eligible}   # normalize relevance 0-1
    chosen, cand = [], list(eligible)
    while cand and len(chosen) < k:
        if not chosen:
            i = max(cand, key=lambda c: rn[c])
        else:
            i = max(cand, key=lambda c: MMR_LAMBDA * rn[c]
                    - (1 - MMR_LAMBDA) * max(float(mat[c] @ mat[s]) for s in chosen))
        chosen.append(i); cand.remove(i)
    return chosen


def _disinterest_mult(adv_toks: set[str], persona: dict) -> float:
    dis = set(_TOK.findall(" ".join(persona.get("disinterested_in", [])).lower()))
    return DISINTEREST_MULT if (adv_toks & dis) else 1.0


class EmbeddingMatcher(Matcher):
    name = "embedding"

    def rank_publishers(self, profile: AdvertiserProfile) -> list[PublisherMatch]:
        pubs = load_publishers()
        scores, _, _ = _score(_adv_text(profile), [_pub_text(p) for p in pubs])
        scores = scores.astype(np.float32).copy()
        for i, p in enumerate(pubs):                 # exact category match -> small bonus
            if profile.product_category and p["category"] == profile.product_category:
                scores[i] += 0.10
        k = _count_by_mass(scores, PUB_MIN, PUB_MAX)
        rec = set(np.argsort(scores)[::-1][:k].tolist())
        out = []
        for i, p in enumerate(pubs):
            s = round(float(np.clip(scores[i], 0, 1)) * 100, 1)
            out.append(PublisherMatch(
                publisher_id=p["id"], publisher_name=p["name"], score=s,
                factors=[FactorScore(name="embedding_similarity", raw=s, weight=1.0)],
                reason=f"embedding match on category/audience (score {s})", excluded=i not in rec))
        return sorted(out, key=lambda m: m.score, reverse=True)

    def rank_personas(self, profile: AdvertiserProfile) -> list[PersonaMatch]:
        pers = load_personas()
        adv_text = _adv_text(profile)
        adv_toks = set(_TOK.findall(adv_text.lower()))
        scores, mat, method = _score(adv_text, [_per_text(p) for p in pers])
        scores = scores.astype(np.float32).copy()
        conflict = []
        for i, p in enumerate(pers):                 # (1) disinterest multiplier
            m = _disinterest_mult(adv_toks, p)
            scores[i] *= m
            conflict.append(m < 1.0)
        k = _count_by_mass(scores, MIN_PERSONAS, TOP_PERSONAS)                 # (2) consistent 3-5
        chosen = set(_mmr(mat, scores, list(range(len(pers))), k))            # (3) diverse pick
        out = []
        for i, p in enumerate(pers):
            s = round(float(np.clip(scores[i], 0, 1)) * 100, 1)
            out.append(PersonaMatch(
                persona_id=p["id"], persona_name=p["name"], score=s,
                factors=[FactorScore(name="embedding_similarity", raw=s, weight=1.0)],
                disinterest_conflict=conflict[i], reason=f"embedding affinity match (score {s})",
                selected=i in chosen))
        return sorted(out, key=lambda m: m.score, reverse=True)
