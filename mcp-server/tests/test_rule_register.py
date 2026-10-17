"""Governance of the rule register (mcp-server/rules/register.json).

These tests make the build fail when a rule loses its legal basis, its tests, or its review date passes:
regulatory drift is caught by CI instead of by an auditor.
"""

import datetime as dt
import json
import re
from pathlib import Path

import engine
import pytest
from rules import render

TESTS = Path(__file__).parent
REQUIRED = {"id", "check", "type", "intent", "engine_behaviour", "applies", "since", "history", "tests",
            "last_reviewed", "review_every_months"}
LEVELS = {"primary", "secondary", "unverified", "n/a"}


def add_months(day: dt.date, months: int) -> dt.date:
    y, mth = divmod(day.month - 1 + months, 12)
    return dt.date(day.year + y, mth + 1, min(day.day, 28))


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


def test_register_version_matches_engine():
    assert engine.REGISTER["rules_version"] == engine.RULES_VERSION


@pytest.mark.parametrize("rule", engine.REGISTER["rules"], ids=lambda r: r["id"])
def test_rule_is_complete(rule):
    assert REQUIRED <= set(rule), REQUIRED - set(rule)
    assert rule["type"] in {"compliance", "cross_check", "safety"}
    for a in rule["applies"]:
        assert a["market"] in {"BR", "US", "EU", "ALL"}
        assert a["citation"]
        assert a["content_verified"] in LEVELS and a["effective_source"] in LEVELS
        if a["effective_from"]:
            dt.date.fromisoformat(a["effective_from"])


def test_rule_ids_are_unique():
    ids = [r["id"] for r in engine.REGISTER["rules"]]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("rule", engine.REGISTER["rules"], ids=lambda r: r["id"])
def test_every_rule_points_to_existing_tests(rule):
    assert rule["tests"], "a rule without a test cannot change safely"
    for ref in rule["tests"]:
        file, _, name = ref.partition("::")
        source = (TESTS / file).read_text(encoding="utf-8")
        assert re.search(rf"^def {re.escape(name)}\(", source, re.M), ref


@pytest.mark.parametrize("rule", engine.REGISTER["rules"], ids=lambda r: r["id"])
def test_no_review_is_overdue(rule):
    due = add_months(dt.date.fromisoformat(rule["last_reviewed"]), rule["review_every_months"])
    assert dt.date.today() <= due, f'{rule["id"]} review was due on {due}'


def test_every_checklist_row_the_engine_emits_has_a_rule(m):
    labels = [
        ("INGREDIENTES: Leite integral, açúcar, soja. ALÉRGICOS: CONTÉM LEITE E SOJA. NÃO CONTÉM GLÚTEN. ZERO LACTOSE. "
         "Produto orgânico. Vegano. Não transgênico. [selo: certified vegan]", "BR"),
        ("INGREDIENTS: Corn syrup, oats, whey (milk). GLUTEN FREE. Organic. Non-GMO. Vegan.", "US"),
        ("Ingredients: soy flour, celery, mustard. Organic. EU Agriculture. Gluten free.", "EU"),
        ("INGREDIENTES: Leite, açúcar. ALÉRGICOS: CONTÉM LEITE. CONTÉM GLÚTEN.", "BR"),
    ]
    seen = set()
    for text, market in labels:
        for row in engine.check_label(text, [], market=market, matcher=m)["compliance"]:
            assert row["rule_id"], row["check"]
            seen.add(row["check"])
    assert set(engine.CHECK_RULE) == seen, set(engine.CHECK_RULE) ^ seen


def test_rule_register_page_is_up_to_date():
    register = json.loads(render.REGISTER.read_text(encoding="utf-8"))
    assert render.PAGE.read_text(encoding="utf-8") == render.render(register), \
        "docs/07-rule-register.md is out of date: run `uv run python rules/render.py` from mcp-server"


def test_unverified_basis_never_passes_or_fails(m, monkeypatch):
    # Pretend the Brazilian gluten statement rule were unverified: the engine must fall back to review.
    rule = engine.RULES["BR-GLUTEN"]
    monkeypatch.setitem(rule["applies"][0], "content_verified", "unverified")
    r = engine.check_label("INGREDIENTES: Farinha de trigo, açúcar.", [], matcher=m)
    row = [c for c in r["compliance"] if c["check"] == "Gluten statement"][0]
    assert row["status"] == "review" and "not yet verified" in row["detail"]
