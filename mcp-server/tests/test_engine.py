import engine
import pytest


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


def check(m, text, avoid, strict=False):
    return engine.check_label(text, avoid, strict, matcher=m)


def test_false_alarms_are_not_dairy(m):
    r = check(m, "INGREDIENTES: Manteiga de cacau, leite de coco, ácido lático.", ["lactose"])
    assert r["verdict"] == "green"


def test_sub_ingredients_are_split(m):
    r = check(m, "INGREDIENTES: Molho shoyu (água, soja, trigo, sal).", ["gluten"])
    assert [i["text"] for i in r["ingredients"]] == ["Molho shoyu", "água", "soja", "trigo", "sal"]


def test_gluten_free_claim_contradiction_escalates(m):
    r = check(m, "INGREDIENTES: Água, extrato de malte de cevada. NÃO CONTÉM GLÚTEN.", [])
    assert [x["rule"] for x in r["mismatches"]] == ["XC1"]
    assert r["escalate_to_human_review"]


def test_allergen_missing_from_statement(m):
    r = check(m, "INGREDIENTES: Farinha de arroz, ovo, soro de leite. ALÉRGICOS: CONTÉM LEITE.", [])
    assert any(x["rule"] == "XC2" and "egg" in x["issue"] for x in r["mismatches"])


def test_zero_lactose_without_lactase(m):
    r = check(m, "INGREDIENTES: Leite integral, açúcar. ZERO LACTOSE.", ["lactose"])
    assert [x["rule"] for x in r["mismatches"]] == ["XC3"]


def test_vegan_claim_with_honey(m):
    r = check(m, "INGREDIENTS: Oats, honey. VEGAN.", ["vegan"])
    assert [x["rule"] for x in r["mismatches"]] == ["XC4"]


def test_strict_turns_unclear_into_red(m):
    text = "INGREDIENTES: Amido modificado, sal."
    assert check(m, text, ["gluten"])["verdict"] == "yellow"
    assert check(m, text, ["gluten"], strict=True)["verdict"] == "red"


def test_unknown_ingredient_is_never_green(m):
    r = check(m, "INGREDIENTS: Zorblax powder, salt.", ["vegan"])
    assert r["ingredients"][0]["status"]["vegan"] == "yellow"


def test_no_list_is_insufficient(m):
    assert check(m, "", ["gluten"])["verdict"] == "insufficient"
