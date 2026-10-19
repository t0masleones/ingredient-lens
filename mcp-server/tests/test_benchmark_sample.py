"""F-28: the frozen benchmark sample measures each market in its own language and is traced to its source dump."""

import json
import sys
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parents[2] / "tests" / "benchmark"
sys.path.insert(0, str(BENCH))
from build_sample import MARKETS, MIN_SCANS, detect_language  # noqa: E402

PRODUCTS = [json.loads(line) for line in (BENCH / "off-products.jsonl").open(encoding="utf-8")]


@pytest.mark.parametrize("text, lang", [
    ("Farinha de trigo enriquecida com ferro e ácido fólico, açúcar, sal.", "pt"),
    ("Sugar, enriched wheat flour, salt, natural flavor.", "en"),
    ("Sucre, farine de blé, huile de tournesol, sel.", "fr"),
    ("Zucker, Weizenmehl, Salz, Emulgator: Lecithine (Soja).", "de"),
    ("Azúcar, harina de trigo, aceite vegetal, sal.", "es"),
    ("Zucchero, farina di frumento, olio di girasole, sale.", "it"),
])
def test_detects_the_language_of_an_ingredient_text(text, lang):
    assert detect_language(text) == lang


@pytest.mark.parametrize("text", ["E330, E211", "Sugar, sucre, wheat flour, farine de blé, salt, sel, milk, lait"])
def test_no_language_when_none_leads_clearly(text):
    assert detect_language(text) is None


def test_every_product_is_in_its_market_language():
    wrong = [(p["market"], p["code"]) for p in PRODUCTS if detect_language(p["ingredients"]) != MARKETS[p["market"]][1]]
    assert not wrong, f"{len(wrong)} products not in their market's language, e.g. {wrong[:5]}"


def test_quality_gate_and_source_are_recorded():
    meta = json.loads((BENCH / "off-products.meta.json").read_text(encoding="utf-8"))
    assert len(meta["source_sha256"]) == 64 and meta["filters"]["min_scans"] == MIN_SCANS
    assert all((p["scans"] or 0) >= MIN_SCANS[p["market"]] for p in PRODUCTS)
    assert len({p["code"] for p in PRODUCTS}) == len(PRODUCTS)
    for market, (_, _, n) in MARKETS.items():
        assert meta["markets"][market]["kept"] == sum(p["market"] == market for p in PRODUCTS)
