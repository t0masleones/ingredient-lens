# 07 - Rule register

> [!NOTE]
> Generated from [`register.json`](../mcp-server/rules/register.json) by [`render.py`](../mcp-server/rules/render.py). Do not edit this page: change the register, run `uv run python rules/render.py` from `mcp-server`, and commit both. A test fails when they differ.

**Rules version 0.6.1** · register updated 2026-10-17 · 16 rules: 7 compliance checks, 5 cross-checks, 4 safety rules · first review due 2027-04-17

The register is the single source of the legal basis the rules engine cites. Every row of the compliance checklist and every mismatch that `check_label` returns carries its `rule_id`, the citation, the date the rule applies from and how well that basis was checked, so a reviewer can trace any result to the text of the law. The engine reads this file at start-up; nothing about the legal basis is written in the prompt.

## How to read it

| Mark | Basis checked against | Effect in the engine |
|---|---|---|
| ✅ Primary | The official text | The check can pass or fail |
| 🟡 Secondary | A reputable secondary source (agency guidance, legal database, trade body) | The check can pass or fail; confirm against the official text before a pilot |
| ⚪ Unverified | Not checked yet | A checklist row never passes or fails there: it is always review. A cross-check still sends the label to a person, and its mismatch says the basis is unverified |
| n/a | No legal text applies (a project safety rule or a consistency check) | — |

> [!WARNING]
> **Not yet verified:** XC5 (BR, US, EU). Until someone reads the official text and updates the register, a checklist row on these rules returns review, and a contradiction they find is escalated with `content_verified: unverified`, never resolved by the tool.

## Rules

| Rule | Check | Type | Basis checked | Next review |
|---|---|---|---|---|
| [ALG-DECL](#alg-decl) | Allergen declaration | Compliance check | BR 🟡 · US ✅ · EU ✅ | 2027-04-17 |
| [BR-GLUTEN](#br-gluten) | Gluten statement | Compliance check | BR 🟡 | 2027-04-17 |
| [BR-LACTOSE-STMT](#br-lactose-stmt) | "Contém lactose" statement | Compliance check | BR 🟡 | 2027-04-17 |
| [XC1](#xc1) | Gluten-free claim | Cross-check | BR 🟡 · US ✅ · EU ✅ | 2027-04-17 |
| [XC2](#xc2) | Allergen statement completeness | Cross-check | BR 🟡 · US ✅ · EU ✅ | 2027-04-17 |
| [XC3](#xc3) | Lactose-free claim | Cross-check | BR 🟡 · US n/a · EU n/a | 2027-04-17 |
| [XC4](#xc4) | Vegan claim | Cross-check | All 🟡 | 2027-10-17 |
| [XC5](#xc5) | Organic claim with a declared GMO | Cross-check | BR ⚪ · US ⚪ · EU ⚪ | 2027-04-17 |
| [GMO-LABEL](#gmo-label) | GMO labelling | Compliance check | BR 🟡 · US 🟡 · EU ✅ | 2027-04-17 |
| [ORGANIC](#organic) | Organic claim | Compliance check | BR 🟡 · US 🟡 · EU 🟡 | 2027-04-17 |
| [NONGMO-CLAIM](#nongmo-claim) | Non-GMO claim | Compliance check | All 🟡 | 2027-10-17 |
| [CERT-MARK](#cert-mark) | Other certification mark | Compliance check | All 🟡 | 2027-10-17 |
| [INGEST-GATE](#ingest-gate) | Transcription confidence | Safety rule | All n/a | 2027-10-17 |
| [SAFE-URGENT](#safe-urgent) | Symptoms described now | Safety rule | All n/a | 2027-10-17 |
| [SAFE-WORDING](#safe-wording) | Never call a product safe | Safety rule | All n/a | 2027-10-17 |
| [SAFE-STRICT](#safe-strict) | STRICT mode | Safety rule | All n/a | 2027-10-17 |

## How the register is governed

| Control | Rule | Enforced by |
|---|---|---|
| Verification | primary = official text read; secondary = reputable secondary source; unverified = not yet checked. A rule whose basis is unverified for a market never returns pass or fail there, only review. | The engine (`compliance_checklist`); test `test_unverified_basis_never_passes_or_fails` |
| Effective dates | Same scale for the date the rule applies from. Unverified dates are shown, never used to turn a check off. | Shown on every checklist row (`effective_from`) |
| Review cadence | Every rule has a next review date. CI fails when a review is overdue, so regulatory drift is caught by the build. | `test_no_review_is_overdue` |
| Change control | A change to a rule's behaviour needs a test, a changelog line and a new rules_version. Disputed mappings and rule changes use the GitHub issue forms in .github/ISSUE_TEMPLATE/. | `test_register_version_matches_engine`, `test_every_rule_points_to_existing_tests`, `test_rule_register_page_is_up_to_date` |
| Coverage | Every checklist row the engine emits names a rule. | `test_every_checklist_row_the_engine_emits_has_a_rule` |

All of these run in continuous integration on every push ([`test_rule_register.py`](../mcp-server/tests/test_rule_register.py)).

### Release process for a rule change

1. Open a **Rule change** issue ([form](../.github/ISSUE_TEMPLATE/rule-change.yml)): market, citation with a link to the official text, the date it applies from, the behaviour expected and an example label.
2. Write the failing test first, with the example label.
3. Change the engine and this rule's entry in the register: `applies`, a `history` line, `tests` and `last_reviewed`.
4. Raise `rules_version` in the register and `RULES_VERSION` in `engine.py`: minor for a new or changed behaviour, patch for a citation or date fix. A test fails when the two differ.
5. Run `uv run python rules/render.py`, `uv run pytest` and `uv run eval_rules.py` (and the benchmark when matching changes), then add a line to the [changelog](../agent/CHANGELOG.md).
6. A second person, the regulatory owner, reviews the pull request. Every result names the rules version, so a past check can be traced to the rules it used.

Disputed ingredient mappings ("this term is not milk") follow the same path with their own [form](../.github/ISSUE_TEMPLATE/disputed-mapping.yml); see [data governance](../mcp-server/data/README.md#governance).

### What the register does not do yet

- **Effective dates are recorded, not applied.** The engine checks every label against the rules in force now; a label printed before a rule applied needs a person (roadmap F-09).
- **Thresholds and each market's allergen list still live in code** (`MARKET_ALLERGENS`); the register cites them. Moving them into data is F-09.
- **The checks were made by the project author, not a regulatory professional.** The ⚪ and 🟡 rows are the first thing to confirm before a pilot.

## Rule details

### ALG-DECL

**Allergen declaration** · Compliance check · since 0.4.0 · last reviewed 2026-10-17 · next review 2027-04-17 (every 6 months)

**Intent.** Every allergen the market requires that appears in the ingredients is declared on the label in the form the market prescribes.

**What the engine does.** n/a when no required allergen is listed; pass when the statement covers them; fail when the statement is missing (BR) or incomplete (XC2); review in the US when the statement is missing (the source may be in parentheses) and always in the EU (emphasis is not visible in text).

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| BR | [RDC 26/2015 (consolidated in RDC 727/2022), Anvisa](https://www.legisweb.com.br/legislacao/?id=286510) | 🟡 Secondary | 2016-07-03 | 🟡 Secondary | Published 3 Jul 2015 with 12 months to adapt; Anvisa refused an extension. |
| US | [FALCPA 2004 (Public Law 108-282); FASTER Act 2021 (sesame)](https://www.fda.gov/food/nutrition-food-labeling-and-critical-foods/food-allergies) | ✅ Primary | 2006-01-01 | ⚪ Unverified | Sesame is a major allergen from 1 Jan 2023 (verified on the FDA page); 2006-01-01 for FALCPA is commonly cited, to verify. |
| EU | [Regulation (EU) No 1169/2011, Article 21 and Annex II](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32011R1169) | ✅ Primary | 2014-12-13 | ⚪ Unverified |  |

**History.** **0.2.0** Statement completeness as cross-check XC2. · **0.4.0** Checklist row per market; each market checks only the allergens it requires. · **0.6.0** Statements printed inside an ingredient's parentheses ("arôme (contient alcool)", "vinagre (contém sulfitos)") no longer end the list or count as the label's allergen statement, and an unclosed parenthesis in OCR text no longer hides the rest of the label; found by reference B and the ingredient-order property in the v0.6 benchmark. · **0.6.1** Shared-facility wording ("atelier qui utilise", "facility that processes", "linha que processa") is a may-contain statement, a short allergen sentence right after it continues its list, and German "glutenhaltiges Getreide" is gluten; found in the F-28 language-checked sample.

**Tests.** [test_safety_and_compliance.py](../mcp-server/tests/test_safety_and_compliance.py): `test_br_complete_label_passes`, `test_br_missing_statements_fail`, `test_us_allergen_without_statement_is_review`, `test_eu_emphasis_is_always_review`; [test_benchmark_findings.py](../mcp-server/tests/test_benchmark_findings.py): `test_parenthetical_contains_is_not_the_allergen_statement`, `test_contains_one_or_more_of_the_following_lists_ingredients`, `test_unclosed_parenthesis_does_not_swallow_the_may_contain_statement`, `test_unclosed_parenthesis_before_contains_keeps_the_list`, `test_trace_and_shared_facility_statements_are_read`

### BR-GLUTEN

**Gluten statement** · Compliance check · since 0.4.0 · last reviewed 2026-10-17 · next review 2027-04-17 (every 6 months)

**Intent.** Every industrialized food in Brazil says either "CONTÉM GLÚTEN" or "NÃO CONTÉM GLÚTEN".

**What the engine does.** pass when either statement is found; fail when neither is found (review when the photo did not capture the whole pack).

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| BR | [Lei 10.674/2003](https://www2.camara.leg.br/legin/fed/lei/2003/lei-10674-16-maio-2003-496699-normaatualizada-pl.html) | 🟡 Secondary | 2003-05-19 | ⚪ Unverified | 19 May 2003 is the publication date in the Diário Oficial; the entry-into-force clause is to verify. |

**History.** **0.2.0** Missing statement reported as a note. · **0.4.0** Checklist row (pass / fail). · **0.6.0** Review instead of fail when the photo did not capture the whole pack.

**Tests.** [test_safety_and_compliance.py](../mcp-server/tests/test_safety_and_compliance.py): `test_br_complete_label_passes`, `test_br_missing_statements_fail`; [test_ingestion_gate.py](../mcp-server/tests/test_ingestion_gate.py): `test_incomplete_photo_turns_missing_statements_into_review`

### BR-LACTOSE-STMT

**"Contém lactose" statement** · Compliance check · since 0.4.0 · last reviewed 2026-10-17 · next review 2027-04-17 (every 6 months)

**Intent.** Foods with more than 100 mg of lactose per 100 g or mL say "CONTÉM LACTOSE".

**What the engine does.** pass when the statement is found; review when dairy is listed without it (the amount cannot be read from text).

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| BR | [RDC 136/2017 (consolidated in RDC 727/2022), Anvisa](https://www.gov.br/anvisa/en/rules-and-regulations/arquivos/rdc-136-2017-e.pdf) | 🟡 Secondary | 2019-02-09 | 🟡 Secondary | Published 9 Feb 2017; mandatory for consumer products from 9 Feb 2019 according to a secondary summary. |

**History.** **0.4.0** Checklist row (pass / review).

**Tests.** [test_safety_and_compliance.py](../mcp-server/tests/test_safety_and_compliance.py): `test_br_dairy_asks_for_lactose_statement`

### XC1

**Gluten-free claim** · Cross-check · since 0.2.0 · last reviewed 2026-10-17 · next review 2027-04-17 (every 6 months)

**Intent.** A gluten-free claim is not contradicted by a gluten source in the ingredients or the allergen statement.

**What the engine does.** Mismatch and checklist fail when a gluten source is listed or declared; in the US, oats alone do not contradict the claim.

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| BR | [Lei 10.674/2003; state health surveillance guidance](https://estado.rs.gov.br/vigilancia-intensifica-fiscalizacao-da-rotulagem-de-alimentos-sem-gluten) | 🟡 Secondary | 2003-05-19 | ⚪ Unverified |  |
| US | [21 CFR 101.91](https://www.govinfo.gov/content/pkg/FR-2013-08-05/html/2013-18813.htm) | ✅ Primary | 2014-08-05 | ✅ Primary | Final rule 5 Aug 2013; compliance date 5 Aug 2014; below 20 ppm. |
| EU | [Regulation (EU) No 828/2014](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0828) | ✅ Primary | 2016-07-20 | ⚪ Unverified |  |

**History.** **0.2.0** Added. · **0.4.0** US oats exception; claims printed before the list.

**Tests.** [test_engine.py](../mcp-server/tests/test_engine.py): `test_gluten_free_claim_contradiction_escalates`; [test_safety_and_compliance.py](../mcp-server/tests/test_safety_and_compliance.py): `test_gluten_free_claim_with_malt_fails`; [test_markets.py](../mcp-server/tests/test_markets.py): `test_gluten_free_oats_claim_is_legal_in_the_us`; [test_review_findings.py](../mcp-server/tests/test_review_findings.py): `test_gluten_free_claim_before_wheat_is_a_mismatch`

### XC2

**Allergen statement completeness** · Cross-check · since 0.2.0 · last reviewed 2026-10-17 · next review 2027-04-17 (every 6 months)

**Intent.** When a label has an allergen statement, it declares every allergen the market requires that the ingredients contain.

**What the engine does.** Mismatch when a required allergen is in the ingredients but not in the statement; allergens the market does not require become a note.

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| BR | [RDC 26/2015 (consolidated in RDC 727/2022)](https://www.legisweb.com.br/legislacao/?id=286510) | 🟡 Secondary | 2016-07-03 | 🟡 Secondary |  |
| US | [FALCPA 2004; FASTER Act 2021](https://www.fda.gov/food/nutrition-food-labeling-and-critical-foods/food-allergies) | ✅ Primary | 2006-01-01 | ⚪ Unverified |  |
| EU | [Regulation (EU) No 1169/2011, Annex II](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32011R1169) | ✅ Primary | 2014-12-13 | ⚪ Unverified |  |

**History.** **0.2.0** Added. · **0.4.0** Market-specific required allergens (BR has no sesame or molluscs). · **0.6.0** Statements printed inside an ingredient's parentheses ("arôme (contient alcool)", "vinagre (contém sulfitos)") no longer end the list or count as the label's allergen statement, and an unclosed parenthesis in OCR text no longer hides the rest of the label; found by reference B and the ingredient-order property in the v0.6 benchmark.

**Tests.** [test_engine.py](../mcp-server/tests/test_engine.py): `test_allergen_missing_from_statement`; [test_markets.py](../mcp-server/tests/test_markets.py): `test_eu_statement_must_declare_mustard`, `test_brazil_does_not_require_mustard_or_sesame`, `test_us_requires_sesame`; [test_benchmark_findings.py](../mcp-server/tests/test_benchmark_findings.py): `test_parenthetical_contains_is_not_the_allergen_statement`

### XC3

**Lactose-free claim** · Cross-check · since 0.2.0 · last reviewed 2026-10-17 · next review 2027-04-17 (every 6 months)

**Intent.** A lactose-free claim with milk ingredients lists lactase (or has a lab result).

**What the engine does.** Mismatch and checklist fail when milk is listed without lactase; review otherwise (the 100 mg threshold needs a lab result).

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| BR | [RDC 135/2017 (consolidated in RDC 727/2022)](https://cfn.org.br/rotulagem-de-lactose-em-alimentos-tem-regra-publicada/) | 🟡 Secondary | 2019-02-09 | 🟡 Secondary |  |
| US | No legal definition of lactose-free; consistency check | n/a | — | — |  |
| EU | No harmonised definition of lactose-free; consistency check | n/a | — | — |  |

**History.** **0.2.0** Added; a lactose-free claim with lactase settles the milk declaration for intolerance (golden case T04).

**Tests.** [test_engine.py](../mcp-server/tests/test_engine.py): `test_zero_lactose_without_lactase`; [test_safety_and_compliance.py](../mcp-server/tests/test_safety_and_compliance.py): `test_br_lactose_free_claim_without_lactase_fails`

### XC4

**Vegan claim** · Cross-check · since 0.2.0 · last reviewed 2026-10-17 · next review 2027-10-17 (every 12 months)

**Intent.** A vegan claim is not contradicted by animal-derived ingredients.

**What the engine does.** Mismatch and checklist fail when animal-derived items are listed; review otherwise (processing aids are invisible; the claim is not verified).

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| All markets | [No legal definition of vegan in BR or the US; consistency check](https://www.registrarcorp.com/blog/keto-vegan-or-plant-based-labeling-on-food-and-beverages/) | 🟡 Secondary | — | — |  |

**History.** **0.2.0** Added.

**Tests.** [test_engine.py](../mcp-server/tests/test_engine.py): `test_vegan_claim_with_honey`

### XC5

**Organic claim with a declared GMO** · Cross-check · since 0.5.0 · last reviewed 2026-10-17 · next review 2027-04-17 (every 6 months)

**Intent.** An organic claim is not contradicted by a declared genetically modified ingredient.

**What the engine does.** Mismatch (escalate) when the label claims organic and declares transgênico / bioengineered / genetically modified.

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| BR | [Lei 10.831/2003; Decreto 6.323/2007 (organic production excludes GMOs)](https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/organicos/arquivos-organicos/IN_18_de_20062014_SELO_BRASILEIRO.pdf) | ⚪ Unverified | 2007-12-27 | ⚪ Unverified |  |
| US | [7 CFR 205.105 (excluded methods)](https://www.ecfr.gov/current/title-7/subtitle-B/chapter-I/subchapter-M/part-205) | ⚪ Unverified | 2002-10-21 | ⚪ Unverified |  |
| EU | [Regulation (EU) 2018/848, Article 11](https://eur-lex.europa.eu/eli/reg/2018/848/oj) | ⚪ Unverified | 2022-01-01 | ⚪ Unverified |  |

**History.** **0.5.0** Added after the agent raised it in an evaluation run (the engine still reported 0.4.0; fixed in 0.6.0).

**Tests.** [test_certifications.py](../mcp-server/tests/test_certifications.py): `test_organic_with_gmo_declared_is_a_contradiction`

### GMO-LABEL

**GMO labelling** · Compliance check · since 0.5.0 · last reviewed 2026-10-17 · next review 2027-04-17 (every 6 months)

**Intent.** Genetically modified content above the market's threshold is disclosed in the market's form.

**What the engine does.** Only for ingredients from crops also grown as GMO: pass when a GMO declaration is found; review otherwise (the GMO share needs supplier records or a PCR result).

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| BR | [Decreto 4.680/2003; Portaria MJ 2.658/2003 (T symbol)](https://www.contabeis.com.br/legislacao/23696/decreto-4680-2003/) | 🟡 Secondary | 2003-04-24 | 🟡 Secondary | Above 1% of the product; STJ confirmed the 1% limit in 2024; PLC 34/2015 status to verify. |
| US | [National Bioengineered Food Disclosure Standard, 7 CFR Part 66](https://www.federalregister.gov/documents/2018/12/21/2018-27283/national-bioengineered-food-disclosure-standard) | 🟡 Secondary | 2022-01-01 | ✅ Primary | Mandatory compliance 1 Jan 2022; 5% per ingredient for inadvertent presence. |
| EU | [Regulation (EC) No 1829/2003, Articles 12-13](https://www.legislation.gov.uk/eur/2003/1829/article/12) | ✅ Primary | 2004-04-18 | ⚪ Unverified | 0.9% per ingredient for adventitious presence. |

**History.** **0.5.0** Added (standards alignment).

**Tests.** [test_certifications.py](../mcp-server/tests/test_certifications.py): `test_gm_crop_without_declaration_is_review`, `test_brazil_transgenic_declaration_passes`, `test_us_bioengineered_disclosure_passes`, `test_no_gm_crop_no_gmo_check`

### ORGANIC

**Organic claim** · Compliance check · since 0.5.0 · last reviewed 2026-10-17 · next review 2027-04-17 (every 6 months)

**Intent.** An organic claim carries the particulars the market requires and rests on a certificate.

**What the engine does.** fail when text shows a required particular is missing (US certifier statement, EU control body code); review otherwise (the certificate must be checked in the certifier's register).

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| BR | [Lei 10.831/2003; Decreto 6.323/2007; IN MAPA 18/2014 (SisOrg seal)](https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/organicos/arquivos-organicos/IN_18_de_20062014_SELO_BRASILEIRO.pdf) | 🟡 Secondary | 2014-06-20 | 🟡 Secondary |  |
| US | [USDA National Organic Program, 7 CFR Part 205 (205.303, 205.304)](https://www.ecfr.gov/current/title-7/subtitle-B/chapter-I/subchapter-M/part-205/subpart-D/section-205.303) | 🟡 Secondary | 2002-10-21 | ⚪ Unverified | Certifier statement per a USDA retail labeling guide; exact eCFR wording to verify. |
| EU | [Regulation (EU) 2018/848, Article 32](https://gs1.eu/wp-content/uploads/2023/09/GS1-in-EU-Organic-Products-Guideline-v1.1.pdf) | 🟡 Secondary | 2022-01-01 | ⚪ Unverified |  |

**History.** **0.5.0** Added; missing US certifier statement or EU code is a fail.

**Tests.** [test_certifications.py](../mcp-server/tests/test_certifications.py): `test_organic_claim_rules_by_market`, `test_eu_organic_without_control_body_code_fails_and_escalates`, `test_eu_organic_with_code_is_review`, `test_us_organic_seal_without_certifier_fails`

### NONGMO-CLAIM

**Non-GMO claim** · Compliance check · since 0.5.0 · last reviewed 2026-10-17 · next review 2027-10-17 (every 12 months)

**Intent.** A non-GMO claim rests on a certificate or a PCR result.

**What the engine does.** Always review; names the GM-crop ingredients and the evidence to ask for.

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| All markets | [Private certification schemes (Non-GMO Project, VLOG, ProTerra); certification by ISO/IEC 17065 bodies](https://www.proterrafoundation.org/wp-content/uploads/2021/03/2021-03-02-PTF-Certification-Procedure.pdf) | 🟡 Secondary | — | — |  |

**History.** **0.5.0** Added.

**Tests.** [test_certifications.py](../mcp-server/tests/test_certifications.py): `test_non_gmo_claim_asks_for_evidence`

### CERT-MARK

**Other certification mark** · Compliance check · since 0.5.0 · last reviewed 2026-10-17 · next review 2027-10-17 (every 12 months)

**Intent.** A certification mark is never accepted from text; the certificate is checked.

**What the engine does.** Always review.

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| All markets | [Certification by bodies accredited to ISO/IEC 17065](https://www.iso.org/standard/46568.html) | 🟡 Secondary | — | — |  |

**History.** **0.5.0** Added.

**Tests.** [test_certifications.py](../mcp-server/tests/test_certifications.py): `test_certification_never_passes_from_text`

### INGEST-GATE

**Transcription confidence** · Safety rule · since 0.6.0 · last reviewed 2026-10-17 · next review 2027-10-17 (every 12 months)

**Intent.** No compliance or safety verdict is issued from a reading that may be wrong (fail-closed).

**What the engine does.** low confidence or no ingredient list: needs_manual_review, no checks run; medium confidence or [?] marks: no item and no verdict can be green, no check can pass, decision at least request_evidence; photo of part of the pack: missing statements are review, not fail.

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| All markets | Project safety requirement (external review, October 2026) | n/a | — | — |  |

**History.** **0.6.0** Added.

**Tests.** [test_ingestion_gate.py](../mcp-server/tests/test_ingestion_gate.py): `test_low_confidence_blocks_all_checks`, `test_unsure_words_never_green`, `test_medium_confidence_turns_passes_into_review`, `test_incomplete_photo_turns_missing_statements_into_review`

### SAFE-URGENT

**Symptoms described now** · Safety rule · since 0.4.0 · last reviewed 2026-10-17 · next review 2027-10-17 (every 12 months)

**Intent.** Symptoms of a reaction get emergency guidance only, before any analysis.

**What the engine does.** verdict urgent, no analysis, emergency numbers (SAMU 192, 911, 112).

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| All markets | Project safety requirement US-08 | n/a | — | — |  |

**History.** **0.4.0** Added to the engine (was prompt-only).

**Tests.** [test_safety_and_compliance.py](../mcp-server/tests/test_safety_and_compliance.py): `test_symptoms_now_return_urgent_without_analysis`, `test_no_false_urgent`

### SAFE-WORDING

**Never call a product safe** · Safety rule · since 0.4.0 · last reviewed 2026-10-17 · next review 2027-10-17 (every 12 months)

**Intent.** A green result only means nothing was found in the text; the agent never says safe.

**What the engine does.** Every result carries the wording to use instead of safe.

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| All markets | Project safety requirement US-07 | n/a | — | — |  |

**History.** **0.4.0** Added to the engine (was prompt-only).

**Tests.** [test_safety_and_compliance.py](../mcp-server/tests/test_safety_and_compliance.py): `test_green_verdict_comes_with_safe_wording`

### SAFE-STRICT

**STRICT mode** · Safety rule · since 0.2.0 · last reviewed 2026-10-17 · next review 2027-10-17 (every 12 months)

**Intent.** For an allergy or celiac disease every unclear item counts as red.

**What the engine does.** yellow becomes red for allergen profiles when strict is true.

| Market | Legal basis | Basis checked | Applies from | Date checked | Note |
|---|---|---|---|---|---|
| All markets | Project safety requirement US-04 | n/a | — | — |  |

**History.** **0.2.0** Added.

**Tests.** [test_engine.py](../mcp-server/tests/test_engine.py): `test_strict_turns_unclear_into_red`
