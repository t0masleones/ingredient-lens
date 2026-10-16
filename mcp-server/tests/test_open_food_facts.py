"""Open Food Facts terms (data/off-terms.csv): coverage gains without new false greens."""

import csv

import engine
import pytest

ANIMAL = {"milk", "egg", "fish", "crustacean", "mollusc"}


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


@pytest.fixture(scope="module")
def off_rows():
    with open(engine.OFF_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def status(m, item, avoid):
    r = engine.check_label(f"INGREDIENTES: {item}.", [avoid], matcher=m)
    return r["ingredients"][0]["status"][avoid]


@pytest.mark.parametrize("item, avoid, level", [
    ("lait écrémé", "lactose", "red"), ("Weizenmehl", "gluten", "red"), ("farina di frumento", "gluten", "red"),
    ("crème de coco", "lactose", "green"), ("Haselnüsse", "tree_nuts", "red"),
])
def test_eu_language_terms(m, item, avoid, level):
    assert status(m, item, avoid) == level


def test_foreign_term_never_replaces_portuguese(off_rows):
    langs = {r["term"]: r["lang"] for r in off_rows}
    assert langs.get("polvo", "pt") in ("pt", "es", "en")


def test_curated_terms_win(m):
    assert m.terms["acucar"].source == "origin-glossary"
    assert m.terms["leite de coco"].source == "lactose-gluten-glossary"


@pytest.mark.parametrize("code, level", [("INS 120", "red"), ("E120", "red"), ("E904", "red"),
                                         ("INS 322", "yellow"), ("E471", "yellow"), ("INS 330", "green")])
def test_additive_codes_are_known_for_vegans(m, code, level):
    assert status(m, f"aditivo {code}", "vegan") == level


def test_e441_is_not_gelatin(m):
    assert status(m, "E441", "vegan") == "green"


def test_lecithin_code_can_be_soy(m):
    assert status(m, "estabilizante INS 322", "soy") == "yellow"


@pytest.mark.parametrize("item, avoid, level", [
    ("semolina", "gluten", "red"), ("bulgur", "gluten", "red"), ("malte", "gluten", "red"),
    ("pão", "gluten", "yellow"), ("breadcrumbs", "gluten", "yellow"),
    ("kefir", "lactose", "red"), ("requeijão", "lactose", "red"),
    ("tofu", "soy", "red"), ("edamame", "soy", "red"), ("óleo de amendoim", "peanut", "red"),
    ("tomate", "gluten", "green"), ("tomate", "lactose", "green"), ("tomate", "vegan", "green"),
])
def test_known_traps(m, item, avoid, level):
    assert status(m, item, avoid) == level


def test_no_allergen_is_ruled_out_without_evidence(off_rows):
    """An imported term may leave an allergen out only if it is vegan (animal groups) or plainly a plant
    food such as fruit or spice (plant groups); every other group must be declared or flagged."""
    for r in off_rows:
        if r["note"].startswith("Additive"):
            continue
        covered = set(filter(None, (r["allergens"] + ";" + r["may_allergens"]).split(";")))
        if r["origin"] != "non_animal":
            assert ANIMAL <= covered, r["term"]
        assert {"celery", "mustard", "sulphites", "lupin"} <= covered, r["term"]
        # The gluten column must agree with the allergen columns, since the engine reads it first.
        if "gluten" in r["allergens"].split(";"):
            assert r["gluten"] == "red", r["term"]
        elif "gluten" in r["may_allergens"].split(";"):
            assert r["gluten"] == "yellow", r["term"]
