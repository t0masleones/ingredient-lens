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


def test_split_derivados_statement_is_read(m):
    # Found by the v0.6 failure buckets: "CONTÉM GLÚTEN. DERIVADOS DE SOJA" hid the soy declaration.
    r = check(m, "INGREDIENTES: Farinha de trigo, aveia, açúcar. CONTÉM GLÚTEN. DERIVADOS DE SOJA.", ["soy"])
    assert "soy" in r["statements"]["contains"]
    assert r["verdict"] == "red"


# Found by reference B in the v0.6 benchmark (40% of French statements "missed" an allergen): a statement printed
# inside an ingredient's parentheses ended the list, so every ingredient after it was dropped.
@pytest.mark.parametrize("text, market", [
    ("INGREDIENTES: açúcar, vinagre (contém sulfitos), gelatina, sal.", "BR"),
    ("Ingrédients : farine de blé, arôme naturel (contient alcool), sucre, gélatine de porc, sel.", "EU"),
    ("INGREDIENTS: coconut flakes 28% (contains: sulfur dioxide), sugar, gelatin.", "EU"),
    ("Zutaten: Zucker, Aroma (enthält Alkohol), Gelatine, Salz.", "EU"),
])
def test_contains_inside_parentheses_does_not_end_the_list(m, text, market):
    r = check(m, text, ["vegan"], market=market)
    assert r["verdict"] == "red"                                   # was 🟢 or 🟡: the gelatin was dropped
    assert not r["statements"]["allergen_statement_found"]


def test_parenthetical_contains_is_not_the_allergen_statement(m):
    r = check(m, "Ingrédients : farine de BLÉ, œufs, arôme (contient alcool), beurre.", [], market="EU")
    assert not any(x["rule"] == "XC2" for x in r["mismatches"])


def test_contains_one_or_more_of_the_following_lists_ingredients(m):
    text = ("INGREDIENTS: Potatoes, Vegetable Oil Contains One Or More Of The Following: Corn, Soybean, Sunflower, "
            "Seasoning (Whey, Nonfat Dry Milk), Gelatin.")
    r = check(m, text, ["vegan"], market="US")
    assert "Gelatin" in [i["text"] for i in r["ingredients"]] and r["verdict"] == "red"
    assert r["statements"]["contains"] == []                       # the label does not declare milk
    row = [c for c in r["compliance"] if c["check"] == "Allergen declaration"][0]
    assert row["status"] != "pass"


def test_may_contain_inside_parentheses_is_a_statement(m):
    r = check(m, "INGREDIENTES: açúcar, chocolate (cacau, pode conter leite), sal.", ["milk"])
    assert r["verdict"] == "yellow" and "milk" in r["statements"]["may_contain"]
    assert "cacau" in [i["text"] for i in r["ingredients"]]


def test_gluten_statement_inside_parentheses_is_read(m):
    assert check(m, "INGREDIENTES: farinha de trigo (contém glúten), açúcar.", [])["statements"]["gluten"] == "contains"


def test_unclosed_parenthesis_does_not_swallow_the_may_contain_statement(m):
    # OCR text from the v0.6 benchmark: the "(" after "farinha de trigo" never closes, which made the traces
    # statement part of an ingredient (read as "contains").
    text = ("INGREDIENTS: Peito de frango (60%), farinha de trigo (glutenamido de milho, cebola em pó, sal, "
            "aromas (contém leite e soja) especiarias, alho. Pode conter vestígios de: crustáceos, ovo, peixe.")
    r = check(m, text, ["egg"])
    assert r["verdict"] == "yellow" and "egg" in r["statements"]["may_contain"]


def test_unclosed_parenthesis_before_contains_keeps_the_list(m):
    # A margarine in the v0.6 sample: "(CONTEM OLEO DE SOJA, AGUA, …" never closes, and the whey after it was lost.
    text = ("INGREDIENTES: óleos vegetais (contém óleo de soja, água, sal, soro de leite, gelatina. "
            "ALÉRGICOS: CONTÉM LEITE E SOJA.")
    r = check(m, text, ["vegan"])
    assert "gelatina" in [i["text"] for i in r["ingredients"]] and r["verdict"] == "red"
    assert r["statements"]["allergen_statement_found"]


def test_a_rewritten_list_gives_the_same_verdict(m):
    # The metamorphic order check rewrites the list from the parsed items, so no item may start a statement.
    text = "INGREDIENTES: açúcar, aroma (contém leite e soja), gelatina, sal."
    items = [i["text"] for i in check(m, text, ["vegan"])["ingredients"]]
    assert "leite e soja" in items
    for order in (items, items[::-1]):
        assert check(m, "INGREDIENTES: " + ", ".join(order) + ".", ["vegan"])["verdict"] == "red"


def test_allergen_header_ends_the_list_after_an_unclosed_parenthesis(m):
    r = check(m, "INGREDIENTES: farinha de trigo (enriquecida com ferro, açúcar, sal. ALÉRGICOS: CONTÉM LEITE.", [])
    assert r["statements"]["allergen_statement_found"] and "milk" in r["statements"]["contains"]


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


@pytest.mark.parametrize("text, avoid", [
    # F-28 sample (v0.6): German compound "glutenhaltigem Getreide" was not read in a trace statement.
    ("Zutaten: Kurkuma. Kann Spuren von glutenhaltigem Getreide, Soja und Senf enthalten.", "gluten"),
    # F-28 sample (v0.6): shared-facility wording, with the allergen list split by a period.
    ("Ingrédients: Purée de pomme de terre, sel. Produit élaboré dans un atelier qui utilise : gluten. lait.", "milk"),
    ("Ingrédients: Purée de pomme de terre, sel. Produit élaboré dans un atelier qui utilise : gluten. lait.", "gluten"),
    ("INGREDIENTS: Sugar, salt. Made in a facility that also processes peanuts.", "peanut"),
])
def test_trace_and_shared_facility_statements_are_read(m, text, avoid):
    assert check(m, text, [avoid], market="EU")["verdict"] == "yellow"
