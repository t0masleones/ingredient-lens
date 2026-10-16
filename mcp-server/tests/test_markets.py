"""EU-only allergens (celery, mustard, sulphites, lupin) and market-specific allergen statements."""

import engine
import pytest


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


def check(m, text, avoid, strict=False, market="BR"):
    return engine.check_label(text, avoid, strict, market, matcher=m)


@pytest.mark.parametrize("item, avoid", [
    ("aipo", "celery"), ("celery salt", "celery"), ("mostarda", "mustard"), ("mustard seed", "mustard"),
    ("farinha de tremoço", "lupin"), ("metabissulfito de sódio", "sulphites"), ("INS 223", "sulphites"),
    ("E220", "sulphites"),
])
def test_eu_allergens_are_red(m, item, avoid):
    assert check(m, f"INGREDIENTES: Água, {item}.", [avoid])["verdict"] == "red"


@pytest.mark.parametrize("alias, group", [("aipo", "celery"), ("mostarda", "mustard"), ("sulfitos", "sulphites"),
                                          ("tremoço", "lupin"), ("gergelim", "sesame")])
def test_profile_aliases(alias, group):
    assert engine.normalize_avoid([alias]) == [group]


def test_eu_statement_must_declare_mustard(m):
    text = "INGREDIENTS: Water, vinegar, mustard seed. CONTAINS: EGG."
    assert [x["rule"] for x in check(m, text, [], market="EU")["mismatches"]] == ["XC2"]


def test_brazil_does_not_require_mustard_or_sesame(m):
    r = check(m, "INGREDIENTES: Água, vinagre, mostarda, gergelim. ALÉRGICOS: CONTÉM OVO.", [], market="BR")
    assert r["mismatches"] == []
    assert any("mustard" in n and "sesame" in n for n in r["notes"])


def test_us_requires_sesame(m):
    r = check(m, "INGREDIENTS: Flour, sesame. CONTAINS: WHEAT.", [], market="US")
    assert any("sesame" in x["issue"] for x in r["mismatches"])


@pytest.mark.parametrize("text, may", [
    ("Zutaten: Zucker, Kakaobutter. Kann Spuren von Milch und Haselnüssen enthalten.", ["milk", "tree_nuts"]),
    ("Ingrédients : sucre, beurre de cacao. Peut contenir des traces de lait.", ["milk"]),
    ("Ingredienti: zucchero, burro di cacao. Può contenere latte.", ["milk"]),
])
def test_eu_language_statements(m, text, may):
    r = check(m, text, ["milk"], market="EU")
    assert r["statements"]["may_contain"] == may
    assert [i["text"] for i in r["ingredients"]][0] in ("Zucker", "sucre", "zucchero")
    assert r["verdict"] == "yellow"


def test_oats_by_market(m):
    text = "INGREDIENTS: Whole grain oats, sugar, salt."
    assert check(m, text, ["gluten"], market="US")["verdict"] == "yellow"
    assert check(m, text, ["gluten"], strict=True, market="US")["verdict"] == "red"
    assert check(m, text, ["gluten"], market="BR")["verdict"] == "red"
    assert check(m, text, ["gluten"], market="EU")["verdict"] == "red"


def test_gluten_free_oats_claim_is_legal_in_the_us(m):
    r = check(m, "INGREDIENTS: Gluten free oats, honey. GLUTEN FREE.", [], market="US")
    assert r["mismatches"] == []
    assert [x["rule"] for x in check(m, "INGREDIENTES: Aveia, mel. NÃO CONTÉM GLÚTEN.", [], market="BR")[
        "mismatches"]] == ["XC1"]


def test_corn_semolina_is_not_wheat(m):
    assert check(m, "INGREDIENTS: Enriched corn meal, salt.", ["gluten"], market="US")["verdict"] != "red"


def test_contains_statement_reads_eu_allergens(m):
    r = check(m, "INGREDIENTS: Water, salt. CONTAINS: CELERY, MUSTARD.", ["celery"], market="EU")
    assert r["statements"]["contains"] == ["celery", "mustard"]
    assert r["verdict"] == "red"
