"""Rule INGEST-GATE (fail-closed ingestion) and audit traceability (v0.6, after the external review)."""

import engine
import pytest


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


CLEAN_BR = "INGREDIENTES: Farinha de trigo, açúcar, ovo. ALÉRGICOS: CONTÉM TRIGO E OVO. CONTÉM GLÚTEN."


def check(m, text, avoid=(), **kw):
    return engine.check_label(text, list(avoid), matcher=m, **kw)


# ---------------------------------------------------------------- the gate

def test_low_confidence_blocks_all_checks(m):
    r = check(m, CLEAN_BR, ["lactose"], source="photo", transcription_confidence="low")
    assert r["verdict"] == "needs_manual_review"
    assert r["next_step"] == "manual_review"
    assert "compliance" not in r and "ingredients" not in r
    assert r["ingestion"]["gate"] == "blocked"


def test_unsure_words_never_green(m):
    r = check(m, "INGREDIENTES: Arroz, sal, extrato de mal[?]e.", ["gluten"], source="photo",
              transcription_confidence="medium")
    unsure = [i for i in r["ingredients"] if "[?]" in i["text"]]
    assert unsure and all(i["status"]["gluten"] != "green" for i in unsure)
    assert r["verdict"] != "green"


def test_unsure_words_are_red_in_strict_mode(m):
    r = check(m, "INGREDIENTES: Arroz, sal, extrato de mal[?]e.", ["gluten"], strict=True, source="photo")
    assert r["verdict"] == "red"


def test_medium_confidence_turns_passes_into_review(m):
    r = check(m, CLEAN_BR, source="photo", transcription_confidence="medium")
    assert r["ingestion"]["gate"] == "degraded"
    assert all(c["status"] != "pass" for c in r["compliance"])
    assert r["next_step"] == "request_evidence"
    assert any(e.startswith("Transcription") for e in r["evidence_needed"])


def test_high_confidence_text_is_unchanged(m):
    r = check(m, CLEAN_BR)
    assert r["ingestion"]["gate"] == "passed"
    assert r["next_step"] == "ready_for_sign_off"


def test_incomplete_photo_turns_missing_statements_into_review(m):
    text = "INGREDIENTES: Farinha de trigo, açúcar, ovo."
    full = {c["check"]: c["status"] for c in check(m, text, source="photo", complete_pack=True)["compliance"]}
    part = {c["check"]: c["status"] for c in check(m, text, source="photo", complete_pack=False)["compliance"]}
    assert full["Gluten statement"] == "fail" and full["Allergen declaration"] == "fail"
    assert part["Gluten statement"] == "review" and part["Allergen declaration"] == "review"


def test_unknown_confidence_value_is_treated_as_medium(m):
    assert check(m, CLEAN_BR, transcription_confidence="maybe")["ingestion"]["transcription_confidence"] == "medium"


# ---------------------------------------------------------------- traceability (audit defensibility)

def test_same_input_same_check_id_and_versions(m):
    a, b = check(m, CLEAN_BR), check(m, CLEAN_BR)
    assert a["check_id"] == b["check_id"] and len(a["check_id"]) == 12
    assert a["input_sha256"] == b["input_sha256"]
    assert a["rules_version"] == engine.RULES_VERSION
    assert engine.DATA_HASH in a["data_version"]
    assert check(m, CLEAN_BR + " ")["check_id"] != a["check_id"]


def test_each_match_names_its_data_source(m):
    r = check(m, "INGREDIENTS: whey powder, sugar.", ["milk"], market="US")
    whey = r["ingredients"][0]
    assert whey["matched_terms"] and len(whey["match_sources"]) == len(whey["matched_terms"])
    assert all(s for s in whey["match_sources"])


def test_checklist_rows_carry_rule_id_and_citation(m):
    r = check(m, CLEAN_BR)
    for row in r["compliance"]:
        assert row["rule_id"] in engine.RULES
        assert row["basis"]
    assert {row["rule_id"] for row in r["compliance"]} >= {"ALG-DECL", "BR-GLUTEN"}


def test_mismatches_carry_their_legal_basis(m):
    r = check(m, "INGREDIENTES: Água, extrato de malte de cevada. NÃO CONTÉM GLÚTEN.")
    xc1 = [x for x in r["mismatches"] if x["rule"] == "XC1"][0]
    assert "10.674" in xc1["citation"]
