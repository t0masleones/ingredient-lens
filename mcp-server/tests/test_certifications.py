"""GMO labelling and certification claims in the Analyst compliance checklist (v0.5)."""

import engine
import pytest


@pytest.fixture(scope="module")
def m():
    return engine.Matcher()


def checks(m, text, market="BR"):
    r = engine.check_label(text, [], market=market, matcher=m)
    return {c["check"]: c for c in r["compliance"]}


@pytest.mark.parametrize("market, basis", [("BR", "Decreto 4.680/2003"), ("US", "7 CFR Part 66"), ("EU", "1829/2003")])
def test_gm_crop_without_declaration_is_review(m, market, basis):
    c = checks(m, "INGREDIENTS: Corn starch, soybean oil, salt. CONTAINS: SOY.", market)["GMO labelling"]
    assert c["status"] == "review"
    assert basis in c["basis"]
    assert "ISO/IEC 17025" in c["detail"]


def test_brazil_transgenic_declaration_passes(m):
    text = "INGREDIENTES: Óleo de soja, sal. ALÉRGICOS: CONTÉM SOJA. NÃO CONTÉM GLÚTEN. [símbolo T] Contém soja transgênica."
    assert checks(m, text)["GMO labelling"]["status"] == "pass"


def test_us_bioengineered_disclosure_passes(m):
    text = "INGREDIENTS: Corn syrup, sugar. Contains a bioengineered food ingredient."
    assert checks(m, text, "US")["GMO labelling"]["status"] == "pass"


def test_no_gm_crop_no_gmo_check(m):
    assert "GMO labelling" not in checks(m, "INGREDIENTES: Arroz, sal. NÃO CONTÉM GLÚTEN.")


def test_non_gmo_claim_asks_for_evidence(m):
    c = checks(m, "INGREDIENTS: Soybeans, water. NON-GMO PROJECT VERIFIED.", "US")
    assert c["Non-GMO claim"]["status"] == "review"
    assert "soybeans" in c["Non-GMO claim"]["detail"].lower()
    assert c["Other certification mark"]["status"] == "review"


@pytest.mark.parametrize("market, text, needle", [
    ("BR", "INGREDIENTES: Arroz integral orgânico, sal. NÃO CONTÉM GLÚTEN. Produto orgânico.", "SisOrg"),
    ("US", "INGREDIENTS: Organic oats, organic honey. USDA ORGANIC. Certified organic by Example Certifier.",
     "Certified organic by"),
    ("EU", "Ingredients: organic wheat flour, water, salt. DE-ÖKO-001. EU Agriculture.", "control body"),
])
def test_organic_claim_rules_by_market(m, market, text, needle):
    c = checks(m, text, market)["Organic claim"]
    assert c["status"] == "review"
    assert needle in c["detail"]


def test_certification_never_passes_from_text(m):
    r = engine.check_label("INGREDIENTS: Rice flour, salt. CERTIFIED GLUTEN FREE. Certified vegan.", [], market="US",
                           matcher=m)
    marks = [c for c in r["compliance"] if c["check"] == "Other certification mark"]
    assert marks and all(c["status"] == "review" for c in marks)


# ---------------------------------------------------------------- v0.5: decisions and organic particulars

def result(m, text, market="BR", avoid=None):
    return engine.check_label(text, avoid or [], market=market, matcher=m)


def test_eu_organic_without_control_body_code_fails_and_escalates(m):
    r = result(m, "Ingredients: organic maize flour, rapeseed oil, salt. Organic. EU Agriculture.", "EU")
    c = {x["check"]: x for x in r["compliance"]}
    assert c["Organic claim"]["status"] == "fail"
    assert r["next_step"] == "escalate" and r["escalate_to_human_review"]


def test_eu_organic_with_code_is_review(m):
    r = result(m, "Ingredients: organic maize flour, salt. Organic. DE-ÖKO-001. EU Agriculture.", "EU")
    assert {x["check"]: x for x in r["compliance"]}["Organic claim"]["status"] == "review"


def test_us_organic_seal_without_certifier_fails(m):
    r = result(m, "INGREDIENTS: Organic oats, salt. [seal: USDA Organic]", "US")
    assert {x["check"]: x for x in r["compliance"]}["Organic claim"]["status"] == "fail"


def test_claim_needing_evidence_requests_evidence_without_escalating(m):
    text = "INGREDIENTES: Óleo de soja, farinha de milho, sal. ALÉRGICOS: CONTÉM SOJA. NÃO CONTÉM GLÚTEN. [selo: produto orgânico]"
    r = result(m, text)
    assert r["next_step"] == "request_evidence"
    assert not r["escalate_to_human_review"]
    assert any(e.startswith("Organic claim") for e in r["evidence_needed"])
    assert any(e.startswith("GMO labelling") for e in r["evidence_needed"])


def test_clean_label_is_ready_for_sign_off(m):
    r = result(m, "INGREDIENTES: Farinha de trigo, açúcar, ovo. ALÉRGICOS: CONTÉM TRIGO E OVO. CONTÉM GLÚTEN.")
    assert r["next_step"] == "ready_for_sign_off"     # never "approved": a person signs (automation bias)
    assert r["requires_sign_off"] is True


def test_organic_with_gmo_declared_is_a_contradiction(m):
    r = result(m, "INGREDIENTES: Óleo de soja transgênica, sal. ALÉRGICOS: CONTÉM SOJA. NÃO CONTÉM GLÚTEN. Produto orgânico.")
    assert [x["rule"] for x in r["mismatches"]] == ["XC5"]
    assert r["next_step"] == "escalate"


def test_shopper_profile_does_not_escalate_on_a_failed_compliance_check(m):
    r = result(m, "INGREDIENTES: Arroz, sal.", avoid=["lactose"])
    assert {x["check"]: x for x in r["compliance"]}["Gluten statement"]["status"] == "fail"
    assert not r["escalate_to_human_review"]
