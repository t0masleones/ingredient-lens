"""F-25 (what text cannot settle is named) and F-07 (answers without the rules are logged)."""

import engine
import pytest
import review


@pytest.fixture
def audit_log(tmp_path, monkeypatch):
    monkeypatch.setattr(review, "LOG_DIR", tmp_path)
    monkeypatch.setattr(review, "AUDIT", tmp_path / "audit.jsonl")


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


TEXT = "INGREDIENTES: água, açúcar, conservador benzoato de sódio. NÃO CONTÉM GLÚTEN."


def test_analyst_result_names_what_text_cannot_settle(m):
    r = engine.check_label(TEXT, [], matcher=m)
    checks = [x["check"] for x in r["not_verifiable_from_text"]]
    assert any("Additive limits" in c for c in checks) and any("Contaminants" in c for c in checks)
    assert all(x["needs"] for x in r["not_verifiable_from_text"])


def test_gaps_never_change_the_decision(m):
    before = engine.check_label(TEXT, [], matcher=m)["next_step"]
    assert before in ("ready_for_sign_off", "request_evidence", "escalate")
    assert not any(c["check"] in [x["check"] for x in engine.NOT_VERIFIABLE_FROM_TEXT]
                   for c in engine.check_label(TEXT, [], matcher=m)["compliance"])


def test_shopper_result_has_no_analyst_gap_list(m):
    assert engine.check_label(TEXT, ["milk"], matcher=m)["not_verifiable_from_text"] == []


def test_answers_without_check_are_counted(audit_log, m):
    review.audit("check_label", {}, engine.check_label(TEXT, [], matcher=m))
    review.audit("log_answer_without_check", {"reason": "general_question", "mode": "shopper"}, {"mode": "shopper"})
    s = review.usage_stats()
    assert s["answers_without_check"] == 1 and s["answers_without_check_rate"] == 0.5
    assert s["answers_without_check_reasons"] == {"general_question": 1}
