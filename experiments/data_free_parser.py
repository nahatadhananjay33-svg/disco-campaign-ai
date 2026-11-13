"""EXPERIMENT (not part of src/) — a DATA-FREE advertiser parser (v2, robust).

Replaces the LLM parse step with no API, no training data, no fine-tuning:

  1. REGEX        -> price, age range
  2. DICTIONARY   -> geography, business model, values, brand tone, gender, subcategories
  3. EMBEDDINGS   -> product_category, positioning  (pretrained static embeddings)

v2 upgrades (so it stops being over-confident on vague / off-catalog input):
  * PROTOTYPES  — each category is the CENTROID of several seed phrases, not one gloss
                  (captures category variation -> more robust than a single string).
  * KEYWORD BOOST — strong catalog entities ("cat"/"dog"->pet) nudge the score, fixing
                    cases where the embedding drifts (ensemble of embedding + rules).
  * ABSTENTION  — softmax over the scores, then return None ("I don't know") unless the
                  top score clears a FLOOR *and* beats the 2nd by a MARGIN. This is the
                  fix for "embeddings always pick a nearest label."
  * OFF-CATALOG / VAGUE signals — b2b, or too few content words, cap the confidence so the
                  pipeline's gate still catches them (as the LLM would).

Honest limits (still the LLM's job): generating USPs / brand voice / clarifying
questions, and reasoning that needs world knowledge ("between Lululemon and Girlfriend").
"""
from __future__ import annotations

import re
import time
from functools import lru_cache

import numpy as np

from src.derivation import derive_economics
from src.models import AdvertiserProfile, BusinessModel, PricePositioning, TargetGender

# --- tuning knobs (easy to find; may need a small tweak once you see embedding scores) ---
EMBED_FLOOR, EMBED_MARGIN = 0.30, 0.04     # cosine scale
LEX_FLOOR, LEX_MARGIN = 0.10, 0.03         # token-overlap scale (offline fallback)
KEYWORD_BOOST = 0.15                        # added to a category's score per keyword hit
SOFTMAX_TEMP = 12.0                         # sharpness of the probability distribution
MIN_CONTENT_WORDS = 3                       # fewer real words than this -> treat as vague

# --- category PROTOTYPES: a few seed phrases per category (averaged into a centroid) ---
CATEGORY_SEEDS = {
    "apparel": ["clothing and fashion", "activewear leggings and yoga pants",
                "shoes and sneakers", "leather handbags and accessories", "outerwear and jackets"],
    "beauty": ["skincare serums and moisturizer", "makeup and cosmetics", "haircare and shampoo"],
    "beverages": ["soda and sparkling drinks", "functional non-alcoholic beverage",
                  "cold brew coffee and tea"],
    "groceries": ["grocery food and pantry staples", "organic produce", "snacks and protein bars"],
    "home": ["home goods and decor", "bedding and linen sheets", "kitchen and cookware",
             "candles and home fragrance", "refillable cleaning and household products"],
    "instant_delivery": ["instant grocery delivery", "quick commerce convenience store",
                         "fast delivery in minutes"],
    "meal_kits": ["meal kit delivery", "recipe boxes with fresh ingredients", "prepared meal subscription"],
    "pet": ["pet food for dogs and cats", "dog treats and pet supplies",
            "pet subscription box for cat owners", "pet pharmacy and vet products"],
    "wellness_dtc": ["vitamins and dietary supplements", "workout supplements protein and creatine",
                     "wellness and recovery products"],
    "wellness_services": ["spa and massage services", "yoga and fitness classes", "personal training sessions"],
}

# strong entity words that should pull a category regardless of the embedding
CATEGORY_KEYWORDS = {
    "pet": {"pet", "pets", "dog", "dogs", "cat", "cats", "puppy", "kitten", "vet"},
    "beverages": {"drink", "drinks", "beverage", "soda", "sparkling", "coffee", "tea", "kombucha"},
    "apparel": {"clothing", "apparel", "activewear", "leggings", "handbag", "handbags",
                "outerwear", "shoes", "jacket", "shells"},
    "beauty": {"skincare", "makeup", "cosmetics", "haircare", "serum", "fragrance"},
    "home": {"bedding", "linen", "candle", "candles", "cookware", "cleaning", "furniture", "bath"},
    "groceries": {"grocery", "snack", "snacks", "pantry", "bar", "bars"},
    "meal_kits": {"meal", "recipe", "recipes"},
    "wellness_dtc": {"supplement", "supplements", "vitamin", "vitamins", "protein", "creatine", "workout"},
    "wellness_services": {"spa", "yoga", "massage", "fitness", "pilates", "training"},
    "instant_delivery": {"instant", "minutes", "quick"},
}

SUBCATEGORIES = ['activewear','alcohol','basics','bath','bedding','casual','classic','convenience',
 'cookware','fitness_classes','functional_beverages','gifting','gut_health','haircare','home_textiles',
 'household','intimates','kitchen','makeup','meal_kits','natural','non_toxic','organic','pantry',
 'personal_training','pet_food','pet_pharmacy','pet_supplies','plus_size','shoes','skincare','socks',
 'soda_alternative','spa','supplements','sustainable','toys','treats','underwear','vitamins','yoga']

GEOS = {
    "us-east": "US-East", "east coast": "US-East",
    "us-west": "US-West", "west coast": "US-West", "california": "US-West",
    "us-midwest": "US-Midwest", "midwest": "US-Midwest",
    "us-northeast": "US-Northeast", "northeast": "US-Northeast",
    "us-south": "US-South", "south": "US-South",
    "nationwide": "nationwide", "national": "nationwide", "across the us": "nationwide",
}

VALUE_WORDS = ["sustainable", "organic", "natural", "handmade", "vegan", "cruelty free",
               "eco", "ethical", "non toxic", "clean", "recyclable", "refillable",
               "plant based", "fair trade"]
TONE_WORDS = ["playful", "premium", "modern", "minimalist", "bold", "warm", "luxury",
              "fun", "friendly", "sophisticated", "edgy", "calm", "energetic", "refined",
              "approachable", "quirky", "elegant"]
GENDER_FEMALE = {"women", "woman", "female", "moms", "mom", "she", "her", "ladies"}
GENDER_MALE = {"men", "man", "male", "guys"}

POS_CUES = {
    "luxury": ["luxury", "luxurious", "ultra-premium", "high-end", "designer", "exclusive"],
    "premium": ["premium", "upscale", "high quality", "finest"],
    "value": ["budget", "affordable", "value", "cheap", "low-cost", "economical",
              "half the cost", "compete on price", "cheaper"],
}

_STOP = {"we","a","an","the","for","of","and","to","in","our","their","that","this","is","are",
         "it","its","who","want","people","kind","new","thing","them","with","without","you","your"}
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PRICE_RE = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)|(\d[\d,]*(?:\.\d+)?)\s?(?:dollars|usd)", re.I)
_AGE_RE = re.compile(r"(\d{2})\s?(?:-|to|–)\s?(\d{2})")

_EMBED_OK = None  # None=untried, True/False after the first attempt


@lru_cache(maxsize=1)
def _model():
    from model2vec import StaticModel
    return StaticModel.from_pretrained("minishlab/potion-base-8M")


def _embed(texts) -> np.ndarray:
    mat = np.asarray(_model().encode(list(texts)), dtype=np.float32)
    return mat / np.clip(np.linalg.norm(mat, axis=-1, keepdims=True), 1e-9, None)


@lru_cache(maxsize=1)
def _prototypes():
    """One L2-normalized centroid embedding per category (mean of its seed phrases)."""
    names = list(CATEGORY_SEEDS)
    protos = []
    for n in names:
        c = _embed(CATEGORY_SEEDS[n]).mean(axis=0)
        protos.append(c / max(np.linalg.norm(c), 1e-9))
    return names, np.vstack(protos)


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _softmax(x: np.ndarray, temp: float) -> np.ndarray:
    z = (x - x.max()) * temp
    e = np.exp(z)
    return e / e.sum()


def _category_scores(text: str, toks: set[str]) -> tuple[list[str], np.ndarray, str]:
    """Raw per-category scores. Embeddings if available, else lexical overlap. Then a
    keyword boost is added to both (ensemble of semantics + strong entity words)."""
    global _EMBED_OK
    if _EMBED_OK is not False:
        try:
            names, mat = _prototypes()
            scores = mat @ _embed([text])[0]
            _EMBED_OK, method = True, "embedding"
        except Exception:
            _EMBED_OK = False
    if _EMBED_OK is False:
        names = list(CATEGORY_SEEDS)
        scores = np.array([
            len(toks & set(_TOKEN_RE.findall(" ".join(CATEGORY_SEEDS[n])))) /
            max(1, len(set(_TOKEN_RE.findall(" ".join(CATEGORY_SEEDS[n])))))
            for n in names], dtype=np.float32)
        method = "lexical"
    # keyword boost (ensemble)
    scores = scores.copy()
    for i, n in enumerate(names):
        if toks & CATEGORY_KEYWORDS.get(n, set()):
            scores[i] += KEYWORD_BOOST
    return names, scores, method


def _classify_category(text: str) -> tuple[str | None, float, str]:
    """Return (category_or_None, probability, method). Abstains (None) when the top
    score is below a floor OR doesn't beat the runner-up by a margin."""
    toks = _tokens(text)
    names, scores, method = _category_scores(text, toks)
    order = np.argsort(scores)[::-1]
    top, second = float(scores[order[0]]), float(scores[order[1]])
    prob = float(_softmax(scores, SOFTMAX_TEMP)[order[0]])
    floor, margin = (EMBED_FLOOR, EMBED_MARGIN) if method == "embedding" else (LEX_FLOOR, LEX_MARGIN)
    if top < floor or (top - second) < margin:
        return None, prob, method            # "I don't know"
    return names[order[0]], prob, method


def _has_phrase(phrase: str, toks: set[str]) -> bool:
    """True only if every word of `phrase` is a whole token (so 'fun' != 'functional')."""
    parts = _TOKEN_RE.findall(phrase.lower())
    return bool(parts) and all(p in toks for p in parts)


def _price(text: str) -> float | None:
    m = _PRICE_RE.search(text)
    if not m:
        return None
    try:
        return float((m.group(1) or m.group(2)).replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _positioning(text: str, price: float | None) -> PricePositioning:
    if price is not None:
        if price < 60:   return PricePositioning.value
        if price < 90:   return PricePositioning.mid
        if price < 130:  return PricePositioning.mid_premium
        if price < 200:  return PricePositioning.premium
        return PricePositioning.luxury
    low = text.lower()
    for tier, cues in POS_CUES.items():
        if any(c in low for c in cues):
            return PricePositioning(tier)
    return PricePositioning.unknown


def parse_advertiser_datafree(text: str) -> AdvertiserProfile:
    toks = _tokens(text)
    low = text.lower()
    content = toks - _STOP

    category, cat_prob, _ = _classify_category(text)
    subs = [s for s in SUBCATEGORIES if all(p in toks for p in s.split("_"))]
    price = _price(text)
    age = f"{(m := _AGE_RE.search(text)).group(1)}-{m.group(2)}" if _AGE_RE.search(text) else None
    positioning = _positioning(text, price)

    geos = sorted({v for k, v in GEOS.items() if k in low})
    gender = (TargetGender.female if toks & GENDER_FEMALE
              else TargetGender.male if toks & GENDER_MALE else None)
    business = (BusinessModel.subscription if "subscription" in low or "subscribe" in low
                else BusinessModel.b2b if "b2b" in low or "business-to-business" in low or "saas" in low
                else BusinessModel.marketplace if "marketplace" in low
                else BusinessModel.dtc if category else None)
    values = sorted({w for w in VALUE_WORDS if _has_phrase(w, toks)})
    tone = sorted({w for w in TONE_WORDS if _has_phrase(w, toks)})

    # --- confidence, with OFF-CATALOG / VAGUE caps so the gate still works ---
    if category is None:
        conf = 0.15                                  # abstained -> gate will ask
    else:
        conf = 0.45 + 0.4 * cat_prob                 # base on the category probability
        for got in (price is not None, bool(subs), bool(values), gender is not None):
            conf += 0.05 if got else 0.0
    if business == BusinessModel.b2b:                # off-catalog for a consumer catalog
        conf = min(conf, 0.30)
    if len(content) < MIN_CONTENT_WORDS:             # too few real words -> vague
        conf = min(conf, 0.30)
    conf = round(min(0.95, conf), 2)

    note = ["data-free parse: USPs / brand voice / clarifying questions not generated"]
    if business == BusinessModel.b2b:
        note.append("looks B2B / off-catalog for a consumer-DTC catalog")

    profile = AdvertiserProfile(
        product_category=category, subcategories=subs, target_gender=gender,
        target_age_range=age, target_geography=geos, price_positioning=positioning,
        price_point_usd=price, brand_tone=tone, values=values, business_model=business,
        confidence=conf, missing_information=note,
    )
    return derive_economics(profile)


if __name__ == "__main__":
    _classify_category("warm up the model")
    print(f"[category engine: {'embeddings' if _EMBED_OK else 'lexical fallback (model offline)'}]")
    samples = [
        "We sell premium vet-formulated dog food on a monthly subscription, for owners of senior dogs.",
        "B2B SaaS for dental practices. We automate their patient recall workflow.",
        "A new kind of thing for moms.",
        "A subscription box for new cat owners. Toys, food samples, a booklet.",
        "idk just try it",
    ]
    for s in samples:
        t0 = time.perf_counter()
        p = parse_advertiser_datafree(s)
        dt = (time.perf_counter() - t0) * 1000
        print(f"\n> {s!r}  ({dt:.2f} ms)")
        print(f"  category={p.product_category}  positioning={p.price_positioning.value}  "
              f"price={p.price_point_usd}  business={getattr(p.business_model,'value',None)}  conf={p.confidence}")
