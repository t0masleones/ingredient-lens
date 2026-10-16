"""Engine errors found by the benchmark on 6,000 real products (v0.4), kept as regression tests."""

import engine
import pytest


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


def check(m, text, avoid, strict=False, market="BR"):
    return engine.check_label(text, avoid, strict, market, matcher=m)


@pytest.mark.parametrize("text, avoid", [
    # A period inside parentheses ended the list: soy lecithin was lost.
    ("INGREDIENTS: MILK CHOCOLATE (SUGAR, MILK. CHOCOLATE, COCOA BUTTER, LECITHIN (SOY), PGPR, NATURAL FLAVOR).", "soy"),
    # A period used as a separator inside the list: skimmed milk powder was lost.
    ("Zutaten: Zucker, Palmöl, HASELNÜSSE (13%). MAGERMILCHPULVER (8,7%), fettarmer Kakao, Emulgator Lecithine (SOJA).",
     "milk"),
    ("INGREDIENTES: Água. proteínas vegetais (soja, ervilha e grão-de-bico), sal, farinha de ervilha.", "soy"),
])
def test_items_after_a_period_inside_the_list_are_read(m, text, avoid):
    assert check(m, text, [avoid])["verdict"] == "red"


def test_a_closing_sentence_still_ends_the_list(m):
    r = check(m, "INGREDIENTS: Oats, sugar. Store in a dry place.", ["gluten"])
    assert [i["text"] for i in r["ingredients"]] == ["Oats", "sugar"]


def test_decimal_comma_is_not_a_separator(m):
    r = check(m, "Ingrédients : chocolat noir 12,5%, sucre, sel.", ["milk"])
    assert [i["text"] for i in r["ingredients"]] == ["chocolat noir 12,5%", "sucre", "sel"]


def test_german_sharp_s_matches_in_upper_case(m):
    text = "Zutaten: Weizenmehl, Weißwein, Salz."
    assert check(m, text, ["gluten"])["verdict"] == check(m, text.upper(), ["gluten"])["verdict"]
    assert engine.normalize("WEISSWEIN") == engine.normalize("Weißwein")


def test_open_food_facts_allergen_underscores(m):
    assert check(m, "Zutaten: _Weizenmehl_, Zucker, _Magermilchpulver_.", ["milk"])["verdict"] == "red"


@pytest.mark.parametrize("text", [
    "Ingrédients : farine de blé, sucre, sel. Peut aussi contenir du lait.",
    "Ingrédients : farine de blé, sucre, sel. Traces éventuelles de lait et d'autres céréales contenant du gluten",
    "Zutaten: Weizenmehl, Zucker. Kann Spuren von Milch enthalten.",
    "Ingredienti: farina di grano, zucchero. Può contenere tracce di latte.",
])
def test_trace_wording_is_may_contain(m, text):
    r = check(m, text, ["milk"], market="EU")
    assert "milk" in r["statements"]["may_contain"]
    assert r["verdict"] == "yellow"


def test_french_wheat_is_gluten(m):
    assert check(m, "Ingrédients : semoule de blé dur, eau.", ["gluten"])["verdict"] == "red"


@pytest.mark.parametrize("item", ["óleo", "vegetable oil", "gordura vegetal"])
def test_unnamed_oil_may_be_soy(m, item):
    assert check(m, f"INGREDIENTES: Atum, água, {item}, sal.", ["soy"])["verdict"] == "yellow"


@pytest.mark.parametrize("item, avoid, level", [
    ("emulsificante", "soy", "yellow"), ("Emulgator", "egg", "yellow"), ("corante", "vegan", "yellow"),
    ("estabilizante", "vegan", "yellow"), ("acidulante", "vegan", "green"), ("riboflavina", "vegan", "green"),
    ("vitamina D3", "vegan", "yellow"), ("sel", "vegan", "green"), ("eau", "lactose", "green"),
])
def test_additive_classes_and_vitamins(m, item, avoid, level):
    assert check(m, f"INGREDIENTES: {item}.", [avoid])["ingredients"][0]["status"][avoid] == level
