"""Overrides as controlled deviations (F-23) and escalation reasons (F-24), after the second external consultation."""

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


def run(m, text, **kw):
    result = engine.check_label(text, [], matcher=m, **kw)
    review.audit("check_label", {}, result)
    return result


CONTRADICTION = "INGREDIENTES: Água, extrato de malte de cevada. NÃO CONTÉM GLÚTEN."      # XC1: critical
REVIEW_ONLY = "INGREDIENTES: Milho, sal. NÃO CONTÉM GLÚTEN. ALÉRGICOS: NÃO CONTÉM. Produto orgânico."


def test_override_needs_a_standard_category(audit_log, m):
    r = run(m, CONTRADICTION)
    out = review.record_decision(r["check_id"], "A. Reviewer", "approve", "lab report")
    assert "error" in out and "supplier_evidence" in out["categories"]


def test_critical_override_needs_evidence_and_a_second_approver(audit_log, m):
    r = run(m, CONTRADICTION)
    base = dict(reason="lab report", reason_category="supplier_evidence")
    assert "evidence" in review.record_decision(r["check_id"], "A", "approve", **base)["error"]
    assert "second approver" in review.record_decision(r["check_id"], "A", "approve", **base,
                                                       evidence="LR-1")["error"]
    assert "second approver" in review.record_decision(r["check_id"], "A", "approve", **base, evidence="LR-1",
                                                       second_reviewer="a")["error"]      # not the same person
    out = review.record_decision(r["check_id"], "A", "approve", **base, evidence="LR-1", second_reviewer="B")
    assert out["override"] and out["second_reviewer"] == "B"


def test_non_critical_override_needs_only_reason_and_category(audit_log, m):
    r = run(m, REVIEW_ONLY)
    assert r["next_step"] != "ready_for_sign_off" and not review.critical_findings(review.find_check(r["check_id"]))
    out = review.record_decision(r["check_id"], "A", "approve", "organic certificate seen in the register",
                                 reason_category="supplier_evidence")
    assert out["override"] and out["critical_findings"] == []


def test_original_finding_is_kept_next_to_the_override(audit_log, m):
    r = run(m, CONTRADICTION)
    review.record_decision(r["check_id"], "A", "approve", "x", reason_category="data_error", evidence="ISSUE-12",
                           second_reviewer="B")
    assert review.find_check(r["check_id"])["result"]["next_step"] == "escalate"


def test_escalation_reasons_and_reviewer_verdict_are_reported(audit_log, m):
    for _ in range(3):
        r = run(m, CONTRADICTION)
        review.record_decision(r["check_id"], "A", "approve", "x", reason_category="data_error", evidence="I-1",
                               second_reviewer="B", escalation_needed=False)
    run(m, "INGREDIENTES: farinha de tr[?]go, açúcar.", source="photo", transcription_confidence="low")
    stats = review.usage_stats()
    reasons = dict(stats["escalation_reasons"])
    assert reasons["XC1"] == 3 and reasons["gate:blocked"] == 1
    assert stats["escalations_not_needed"] == 3 and stats["escalations_judged"] == 3
    assert stats["overrides_by_category"] == {"data_error": 3} and stats["capa_signals"] == ["data_error"]
