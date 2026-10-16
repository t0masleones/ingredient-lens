"""Properties that must hold for any label, checked on the frozen sample of real products.

The full run with metrics is tests/benchmark/run_benchmark.py; this file keeps the safety properties in every
pytest run (one product in four, all profiles that matter for it).
"""

import json
from pathlib import Path

import engine
import pytest

SAMPLE = Path(__file__).parent.parent.parent / "tests" / "benchmark" / "off-products.jsonl"
OFF_TO_GROUP = {"en:milk": "milk", "en:eggs": "egg", "en:fish": "fish", "en:crustaceans": "crustacean",
                "en:molluscs": "mollusc", "en:gluten": "gluten", "en:soybeans": "soy", "en:peanuts": "peanut",
                "en:nuts": "tree_nuts", "en:sesame-seeds": "sesame", "en:celery": "celery", "en:mustard": "mustard",
                "en:lupin": "lupin", "en:sulphur-dioxide-and-sulphites": "sulphites"}
RANK = engine.RANK

products = [json.loads(line) for line in SAMPLE.open(encoding="utf-8")][::4] if SAMPLE.exists() else []
pytestmark = pytest.mark.skipif(not products, reason="benchmark sample not built")


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


def text_of(p):
    return p["ingredients"] if engine.HEADER.search(p["ingredients"]) else f"INGREDIENTS: {p['ingredients']}"


def profiles(p):
    return ["lactose", "gluten", "vegan"] + sorted({OFF_TO_GROUP[a] for a in p["allergens"] if a in OFF_TO_GROUP})


@pytest.mark.parametrize("p", products, ids=lambda p: p["code"])
def test_label_properties(m, p):
    text = text_of(p)
    for avoid in profiles(p):
        normal = engine.check_label(text, [avoid], matcher=m)
        assert engine.check_label(text, [avoid], matcher=m)["verdict"] == normal["verdict"], "not deterministic"
        assert engine.check_label(text.upper(), [avoid], matcher=m)["verdict"] == normal["verdict"], "case-sensitive"
        strict = engine.check_label(text, [avoid], True, matcher=m)
        if normal["verdict"] == "insufficient":    # no ingredient list at all (only claims): ask for the label
            assert strict["verdict"] == "insufficient"
            continue
        assert RANK[strict["verdict"]] >= RANK[normal["verdict"]], "STRICT milder than normal"


@pytest.mark.parametrize("p", products, ids=lambda p: p["code"])
def test_may_contain_never_helps(m, p):
    text = text_of(p).rstrip(". ") + ". May contain milk."
    assert engine.check_label(text, ["milk"], matcher=m)["verdict"] != "green"
