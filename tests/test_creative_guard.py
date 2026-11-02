"""The creative claim-guard: the LLM must not ship a claim the advertiser never made."""
from src.creative_generator import generate_creative
from src.models import AdvertiserProfile


def _profile():
    return AdvertiserProfile(
        product_category="pet", subcategories=["dog_food"],
        unique_selling_points=["grain-free"], values=["vet-formulated"],
    )


def test_regenerates_then_passes_when_retry_is_clean():
    calls = {"n": 0}

    def stub(_):
        calls["n"] += 1
        if calls["n"] == 1:  # invents an unsupported "certified"/"best" claim
            return {"headline": "Certified best food", "body": "Our certified formula is the best.",
                    "messaging_angle": "trust", "reasoning": "x"}
        return {"headline": "Made for senior dogs", "body": "Grain-free, vet-formulated nutrition.",
                "messaging_angle": "health", "reasoning": "fits"}

    c = generate_creative(_profile(), {"id": "persona_004", "name": "The Pet Parent"}, llm_call=stub)
    assert calls["n"] == 2                      # regenerated once
    assert "certified" not in (c.headline + c.body).lower()


def test_strips_offending_sentence_if_retry_still_invents():
    def stub(_):  # every attempt invents "certified"
        return {"headline": "Grain-free food", "body": "Vet-formulated. Our certified formula wins.",
                "messaging_angle": "health", "reasoning": "fits"}

    c = generate_creative(_profile(), {"id": "persona_004", "name": "The Pet Parent"}, llm_call=stub)
    assert "certif" not in c.body.lower()       # offending sentence stripped
    assert "vet-formulated" in c.body.lower()   # supported sentence kept


def test_fabricated_sustainability_claim_and_bad_headline_are_scrubbed():
    # Brand never claims sustainability/supply-chain; every attempt invents them,
    # including in the headline. Guard must strip the body claim and replace the
    # headline with a grounded USP.
    def stub(_):
        return {"headline": "Leather made to last a lifetime",
                "body": "Handcrafted in Florence with full supply chain transparency.",
                "messaging_angle": "ethics", "reasoning": "x"}

    prof = AdvertiserProfile(product_category="apparel", subcategories=["handbags"],
                             unique_selling_points=["handcrafted in Florence"],
                             values=["Italian heritage"])
    c = generate_creative(prof, {"id": "persona_006", "name": "The Sustainability Buyer"}, llm_call=stub)
    blob = (c.headline + " " + c.body).lower()
    assert "supply chain" not in blob and "transparen" not in blob   # fabricated claim gone
    assert "lifetime" not in c.headline.lower()                       # headline scrubbed
    assert "handcrafted" in c.headline.lower()                        # replaced with a real USP


def test_body_never_collapses_to_a_bare_dot():
    # The whole body is one unsupported-claim sentence, every attempt. Stripping it
    # must NOT leave an empty "." body — it falls back to a grounded USP line.
    def stub(_):
        return {"headline": "Travel with timeless elegance",
                "body": "Built on a transparent, sustainable supply chain.",
                "messaging_angle": "heritage", "reasoning": "x"}

    prof = AdvertiserProfile(product_category="apparel", subcategories=["luggage"],
                             unique_selling_points=["hardside luggage and travel organizers"],
                             values=["premium materials"])
    c = generate_creative(prof, {"id": "persona_005", "name": "The Affluent Classic"}, llm_call=stub)
    assert c.body.strip(" .")                      # not empty, not a bare "."
    assert "supply chain" not in c.body.lower()    # fabricated claim still gone
    assert "luggage" in c.body.lower()             # grounded in the real USP
