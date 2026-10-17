"""US-07 (never "safe"), US-08 (symptoms now) and D-07 (Analyst compliance checklist) in the rules engine."""

import engine
import pytest


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


def check(m, text, avoid, strict=False, market="BR"):
    return engine.check_label(text, avoid, strict, market, matcher=m)


# ---------------------------------------------------------------- US-08: symptoms happening now

@pytest.mark.parametrize("text", [
    "I ate this 20 minutes ago and my lips are swelling. INGREDIENTS: peanut butter, sugar, salt.",
    "My throat feels tight. INGREDIENTS: milk, sugar.",
    "I can't breathe properly after eating this cookie",
    "Comi esse biscoito e meus lábios estão inchados. INGREDIENTES: farinha de trigo, amendoim.",
    "Minha garganta está fechando, o que tem nesse produto?",
    "Estou com falta de ar depois de comer isso",
    "Me cuesta respirar después de comer esto",
    "I have hives right now after the snack",
])
def test_symptoms_now_return_urgent_without_analysis(m, text):
    r = check(m, text, ["peanut"])
    assert r["verdict"] == "urgent"
    assert "192" in r["action"] and "911" in r["action"]
    assert "ingredients" not in r


@pytest.mark.parametrize("text", [
    "INGREDIENTES: Farinha de trigo, açúcar, sal. ALÉRGICOS: CONTÉM TRIGO.",
    "My son had hives last year from peanuts. INGREDIENTS: oats, honey.",
    "INGREDIENTS: Coca leaf extract? no: cola nut extract, caffeine, sugar.",
])
def test_no_false_urgent(m, text):
    assert check(m, text, ["peanut"])["verdict"] != "urgent"


# ---------------------------------------------------------------- US-07: wording instead of "safe"

def test_green_verdict_comes_with_safe_wording(m):
    r = check(m, "INGREDIENTES: Arroz, sal.", ["lactose"])
    assert r["verdict"] == "green"
    assert "I did not find lactose in the text I could read" in r["wording"]
    assert "Never say" in r["wording"]


# ---------------------------------------------------------------- D-07: Analyst compliance checklist

def statuses(r):
    return {c["check"]: c["status"] for c in r["compliance"]}


def test_br_complete_label_passes(m):
    r = check(m, "INGREDIENTES: Farinha de trigo, açúcar, ovo. ALÉRGICOS: CONTÉM TRIGO E OVO. CONTÉM GLÚTEN.", [])
    assert statuses(r) == {"Allergen declaration": "pass", "Gluten statement": "pass"}


def test_br_missing_statements_fail(m):
    r = check(m, "INGREDIENTES: Farinha de trigo, açúcar, ovo.", [])
    assert statuses(r)["Allergen declaration"] == "fail"
    assert statuses(r)["Gluten statement"] == "fail"


def test_br_dairy_asks_for_lactose_statement(m):
    r = check(m, "INGREDIENTES: Leite integral, açúcar. ALÉRGICOS: CONTÉM LEITE. NÃO CONTÉM GLÚTEN.", [])
    assert statuses(r)['"Contém lactose" statement'] == "review"


def test_br_lactose_free_claim_without_lactase_fails(m):
    r = check(m, "INGREDIENTES: Leite integral, açúcar. ALÉRGICOS: CONTÉM LEITE. NÃO CONTÉM GLÚTEN. ZERO LACTOSE.", [])
    assert statuses(r)["Lactose-free claim"] == "fail"


def test_us_allergen_without_statement_is_review(m):
    r = check(m, "INGREDIENTS: Whey (milk), sugar.", [], market="US")
    assert statuses(r)["Allergen declaration"] == "review"


def test_eu_emphasis_is_always_review(m):
    r = check(m, "Ingredients: wheat flour, sugar, celery.", [], market="EU")
    assert statuses(r)["Allergen declaration"] == "review"


def test_gluten_free_claim_with_malt_fails(m):
    r = check(m, "INGREDIENTES: Água, extrato de malte de cevada. NÃO CONTÉM GLÚTEN.", [])
    assert statuses(r)["Gluten-free claim"] == "fail"
