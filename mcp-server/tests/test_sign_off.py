"""Human sign-off with override reasons, traced to the exact check (v0.6, after the external review)."""

import json

import engine
import pytest
import review


@pytest.fixture
def audit_log(tmp_path, monkeypatch):
    monkeypatch.setattr(review, "LOG_DIR", tmp_path)
    monkeypatch.setattr(review, "AUDIT", tmp_path / "audit.jsonl")
    return tmp_path / "audit.jsonl"


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


def run(m, text):
    result = engine.check_label(text, [], matcher=m)
    review.audit("check_label", {"label_chars": len(text)}, result)
    return result


CLEAN = "INGREDIENTES: Farinha de trigo, açúcar, ovo. ALÉRGICOS: CONTÉM TRIGO E OVO. CONTÉM GLÚTEN."
CONTRADICTION = "INGREDIENTES: Água, extrato de malte de cevada. NÃO CONTÉM GLÚTEN."


def test_approving_a_ready_label_needs_no_reason(audit_log, m):
    r = run(m, CLEAN)
    out = review.record_decision(r["check_id"], "A. Reviewer", "approve")
    assert out["decision"] == "approve" and not out["override"]
    assert out["rules_version"] == engine.RULES_VERSION


def test_approving_an_escalated_label_is_an_override_with_reason(audit_log, m):
    r = run(m, CONTRADICTION)
    assert r["next_step"] == "escalate"
    assert "error" in review.record_decision(r["check_id"], "A. Reviewer", "approve")
    out = review.record_decision(r["check_id"], "A. Reviewer", "approve", "Supplier certificate: malt below 20 ppm")
    assert out["decision"] == "approve_with_override" and out["override"]


def test_rejection_needs_a_reason_and_a_named_reviewer(audit_log, m):
    r = run(m, CLEAN)
    assert "error" in review.record_decision(r["check_id"], "A. Reviewer", "reject")
    assert "error" in review.record_decision(r["check_id"], " ", "reject", "wrong artwork")


def test_unknown_check_id_is_refused(audit_log):
    assert "error" in review.record_decision("000000000000", "A. Reviewer", "approve")


def test_audit_log_traces_input_rules_data_and_decision(audit_log, m):
    r = run(m, CLEAN)
    review.record_decision(r["check_id"], "A. Reviewer", "approve")
    rows = [json.loads(line) for line in audit_log.read_text(encoding="utf-8").splitlines()]
    check, decision = rows[0], rows[1]
    assert check["result"]["input_sha256"] == r["input_sha256"]
    assert check["result"]["data_version"] == r["data_version"]
    assert check["compliance"]["BR-GLUTEN"] == "pass"
    assert decision["result"]["check_id"] == r["check_id"] and decision["result"]["reviewer"] == "A. Reviewer"
    stats = review.usage_stats()
    assert stats["decisions"] == {"approve": 1} and stats["override_rate"] == 0
