"""Bugs found in the v0.2.0 code review. Each test failed before the v0.2.1 fix unless marked as a guard."""

import json
import urllib.error

import engine
import pytest
import review


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


def check(m, text, avoid, strict=False):
    return engine.check_label(text, avoid, strict, matcher=m)


def texts(r):
    return [i["text"] for i in r["ingredients"]]


# ---------------------------------------------------------------- the list must not end early

def test_items_after_two_percent_qualifier_are_read(m):
    r = check(m, "INGREDIENTS: Sugar, corn syrup, contains 2% or less of: gelatin, carmine, natural flavor.", ["vegan"])
    assert {"gelatin", "carmine", "natural flavor"} <= set(texts(r))
    assert r["verdict"] == "red"


def test_portuguese_two_percent_qualifier(m):
    r = check(m, "INGREDIENTES: Açúcar, xarope de glicose, contém menos de 2% de: gelatina, carmim.", ["vegan"])
    assert {"gelatina", "carmim"} <= set(texts(r))
    assert r["verdict"] == "red"


def test_vegan_ingredient_names_do_not_end_the_list(m):
    r = check(m, "INGREDIENTS: Sugar, vegan mayonnaise, vegan butter, vegan cheese.", ["vegan"])
    assert texts(r) == ["Sugar", "vegan mayonnaise", "vegan butter", "vegan cheese"]


def test_queijo_vegano_is_kept_whole(m):
    r = check(m, "INGREDIENTES: Açúcar, queijo vegano.", ["lactose"])
    assert texts(r) == ["Açúcar", "queijo vegano"]


def test_coverage_counts_every_item(m):
    r = check(m, "INGREDIENTS: Sugar, contains 2% or less of: gelatin, salt.", ["vegan"])
    assert r["coverage"].startswith("3/3")


def test_guard_vegan_claim_after_the_list_still_counts(m):
    for text in ("INGREDIENTS: Oats, sugar. VEGAN.", "INGREDIENTS: Oats, sugar\nVEGAN"):
        r = check(m, text, ["vegan"])
        assert texts(r) == ["Oats", "sugar"]
        assert r["statements"]["vegan_claim"]


def test_guard_allergen_statement_without_period_ends_the_list(m):
    r = check(m, "INGREDIENTES: Farinha de trigo, açúcar ALÉRGICOS: CONTÉM TRIGO.", ["gluten"])
    assert texts(r) == ["Farinha de trigo", "açúcar"]


# ---------------------------------------------------------------- claims printed before or inside the list
# Found by the benchmark on real Brazilian products (v0.4).

@pytest.mark.parametrize("text, items", [
    ("INGREDIENTES: Sem glúten, Sem lactose, Sem conservantes, Farinha de trigo, água",
     ["Farinha de trigo", "água"]),
    ("INGREDIENTES: CONTÉM FENILALANINA Água Gaseificada, Cafeína, Aroma Natural",
     ["Água Gaseificada", "Cafeína", "Aroma Natural"]),
    ("INGREDIENTES: Feijão carioca, sem conservantes", ["Feijão carioca"]),
])
def test_claims_before_or_inside_the_list(m, text, items):
    assert texts(check(m, text, ["gluten"])) == items


def test_claim_words_never_swallow_an_ingredient(m):
    r = check(m, "INGREDIENTES: SEM GLÚTEN Leite integral, açúcar", ["lactose"])
    assert texts(r) == ["Leite integral", "açúcar"]
    assert r["verdict"] == "red"
    assert check(m, "INGREDIENTS: fat free milk, sugar", ["lactose"])["verdict"] == "red"


def test_gluten_free_claim_before_wheat_is_a_mismatch(m):
    r = check(m, "INGREDIENTES: Sem glúten, Farinha de trigo, água", [])
    assert [x["rule"] for x in r["mismatches"]] == ["XC1"]


# ---------------------------------------------------------------- items that are not ingredients

def test_percentages_and_additive_codes_are_not_unknown_ingredients(m):
    r = check(m, "INGREDIENTES: Leite integral (65%), açúcar, emulsificante lecitina (INS 322), corante (E150a).", ["lactose"])
    assert texts(r) == ["Leite integral", "açúcar", "emulsificante lecitina INS 322", "corante E150a"]


def test_may_contain_without_header_is_a_statement(m):
    r = check(m, "Farinha de trigo, açúcar. Pode conter leite e soja.", ["lactose"])
    assert texts(r) == ["Farinha de trigo", "açúcar"]
    assert r["statements"]["may_contain"] == ["milk", "soy"]
    assert r["verdict"] == "yellow"


# ---------------------------------------------------------------- plant-based dairy alternatives

@pytest.mark.parametrize("name", ["vegan butter", "manteiga vegana", "vegan cheese", "queijo vegano",
                                  "cashew cheese", "coconut cream", "creme de coco"])
def test_plant_based_alternatives_are_not_dairy(m, name):
    r = check(m, f"INGREDIENTS: {name}.", ["lactose", "vegan"])
    assert r["ingredients"][0]["status"]["lactose"] == "green"
    assert r["ingredients"][0]["status"]["vegan"] != "red"


# ---------------------------------------------------------------- review tickets

@pytest.fixture
def queue(tmp_path, monkeypatch):
    monkeypatch.setattr(review, "LOG_DIR", tmp_path)
    monkeypatch.setattr(review, "QUEUE", tmp_path / "review-queue.jsonl")
    monkeypatch.setenv("INGREDIENT_LENS_GITHUB_REPO", "someone/ingredient-lens")
    return tmp_path / "review-queue.jsonl"


def test_ticket_without_token_reports_local_queue(queue, monkeypatch):
    monkeypatch.setattr(review, "_github_token", lambda: None)
    assert review.create_ticket("t", "b")["destination"] == "local queue"
    assert queue.exists()


def test_ticket_is_kept_when_github_fails(queue, monkeypatch):
    def offline(*args, **kwargs):
        raise urllib.error.URLError("offline")
    monkeypatch.setattr(review, "_github_token", lambda: "token")
    monkeypatch.setattr(review.urllib.request, "urlopen", offline)
    out = review.create_ticket("t", "b")
    assert out["destination"] == "local queue"
    assert json.loads(queue.read_text(encoding="utf-8"))["title"] == "t"
