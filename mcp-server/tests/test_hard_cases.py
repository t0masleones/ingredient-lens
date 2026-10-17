"""Hard cases a regulatory team worries about (F-27, from the second external consultation).

On each one the text alone cannot settle the question, so the engine must fail closed: flag, ask for evidence or
escalate, and never mark the label ready for sign-off.
"""

import engine
import pytest


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


def check(m, text, avoid=(), market="BR", **kw):
    return engine.check_label(text, list(avoid), market=market, matcher=m, **kw)


@pytest.mark.parametrize("text, market", [
    ("INGREDIENTES: Arroz, extrato de malte, sal. NÃO CONTÉM GLÚTEN.", "BR"),
    ("INGREDIENTS: Rice flour, barley malt syrup, salt. GLUTEN FREE.", "US"),
    ("Ingredients: maize, wheat starch, sugar. Gluten free.", "EU"),
])
def test_gluten_free_claim_with_a_gluten_source_escalates(m, text, market):
    r = check(m, text, market=market)
    assert r["next_step"] == "escalate" and any(x["rule"] == "XC1" for x in r["mismatches"])


@pytest.mark.parametrize("text", [
    "INGREDIENTES: Farinha de arroz, amido, aroma natural, sal. NÃO CONTÉM GLÚTEN.",
    "INGREDIENTS: Corn, modified food starch, natural flavor, salt. GLUTEN FREE.",
])
def test_gluten_free_claim_with_ambiguous_ingredients_is_never_ready(m, text):
    r = check(m, text, avoid=["gluten"], strict=True, market="US" if "INGREDIENTS" in text else "BR")
    assert r["next_step"] != "ready_for_sign_off" and r["verdict"] == "red"     # STRICT: unclear means red


@pytest.mark.parametrize("text", [
    "INGREDIENTS: Sugar, natural flavors, enzymes, mono- and diglycerides, salt. VEGAN.",
    "INGREDIENTES: Açúcar, aroma natural, culturas lácteas, sal. Vegano.",
])
def test_vegan_claim_with_ambiguous_ingredients_needs_evidence(m, text):
    r = check(m, text, avoid=["vegan"], market="US" if "INGREDIENTS" in text else "BR")
    assert r["verdict"] in ("yellow", "red") and r["next_step"] != "ready_for_sign_off"


@pytest.mark.parametrize("text, group", [
    ("INGREDIENTES: farinha de trigo, açúcar. ALÉRGICOS: CONTÉM TRIGO. PODE CONTER LEITE.", "milk"),
    ("INGREDIENTS: oats, sugar. May contain traces of peanuts.", "peanut"),
    ("Zutaten: Hafer, Zucker. Kann Spuren von Haselnüssen enthalten.", "tree_nuts"),
])
def test_may_contain_is_a_different_class_from_contains(m, text, group):
    r = check(m, text, avoid=[group], market="EU" if "Zutaten" in text else ("US" if "INGREDIENTS" in text else "BR"))
    assert group in r["statements"]["may_contain"] and group not in r["statements"]["contains"]
    assert r["verdict"] == "yellow"
    assert check(m, text, avoid=[group], strict=True,
                 market="EU" if "Zutaten" in text else ("US" if "INGREDIENTS" in text else "BR"))["verdict"] == "red"


@pytest.mark.parametrize("item", ["temperos", "condimento", "realçador de sabor", "aromatizante", "emulsificante"])
def test_umbrella_ingredients_are_never_green_for_an_allergy(m, item):
    r = check(m, f"INGREDIENTES: arroz, {item}, sal.", avoid=["soy"], strict=True)
    assert r["verdict"] != "green"


def test_statement_that_contradicts_the_list_escalates(m):
    r = check(m, "INGREDIENTES: farinha de trigo, soro de leite, açúcar. ALÉRGICOS: CONTÉM TRIGO.")
    assert r["next_step"] == "escalate" and any(x["rule"] == "XC2" for x in r["mismatches"])


def test_additive_without_concentration_is_never_a_pass_on_limits(m):
    # Additive limits by country need the formulation; the checklist has no row that could pass them from text.
    r = check(m, "INGREDIENTES: água, açúcar, conservador benzoato de sódio, corante tartrazina.")
    assert not any("limit" in c["check"].lower() and c["status"] == "pass" for c in r["compliance"])


def test_unsure_reading_of_a_critical_word_blocks_sign_off(m):
    r = check(m, "INGREDIENTES: farinha de [?], açúcar. NÃO CONTÉM GLÚTEN.", source="photo",
              transcription_confidence="medium")
    assert r["next_step"] != "ready_for_sign_off"
    assert all(c["status"] != "pass" for c in r["compliance"])
