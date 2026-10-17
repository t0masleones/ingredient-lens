# 06 - Standards alignment: what a food compliance company delivers, and how close the agent gets

Public information only (FoodChain ID website and public registers, checked 2026-10-17). Independent prototype; no company data or products were used.

## What the company is accredited for and sells
| Area | Standard or accreditation (public) | What customers get |
|---|---|---|
| Product certification (organic, non-GMO, GFSI schemes such as BRCGS, SQF, FSSC 22000) | ISO/IEC 17065 (ANAB in the US, UKAS in the UK, BELAC in Belgium, INMETRO in Brazil, ACCREDIA in Italy); ISO/IEC 17021-1 for management systems (ISO 22000) | A certificate from an impartial, accredited body |
| Testing (GMO, pesticides, contaminants) | ISO/IEC 17025 laboratories in the US, Brazil (INMETRO CRL 1226, REBLAS, MAPA), Germany and Belgium; Non-GMO Project approved labs; VLOG approved lab | Lab results that prove thresholds |
| Organic | USDA NOP accredited certifying agent; EU Regulation 2018/848 control body (Bioagricert, Cosmocert); Japan JAS | Organic certification for export markets |
| Non-GMO | Founding technical administrator of the Non-GMO Project; ProTerra (since 2006, soy in Brazil); VLOG | Non-GMO verification and PCR testing |
| Regulatory compliance and product development | Regulatory Library, Recipes & Specifications, labeling and claims tools | Fewer manual evaluations, no non-compliance surprises |
| Food fraud | Food Fraud Database, supporting GFSI food fraud requirements | Vulnerability assessments |

No public evidence was found of ISO/IEC 27001 or SOC 2 for the company; that is not a statement that it lacks them.

## How the agent maps to it (v0.6)
| Company capability | Agent capability now | Basis in the agent | Gap |
|---|---|---|---|
| Impartial certification (ISO/IEC 17065) | Never certifies and never approves: every result says screening, not certification; certification claims always "review" with the evidence to ask for; a clean label is only "ready for sign-off" by a named reviewer | Instructions (role, Analyst item 5); `compliance` rows "Organic claim", "Non-GMO claim", "Other certification mark"; `record_review_decision` | Cannot query certifiers' public registers (roadmap F-15) |
| Accredited testing (ISO/IEC 17025) | Asks for a lab result whenever a claim depends on a threshold (GMO %, gluten ppm, lactose mg) | `compliance` details; knowledge file `standards-and-certifications.md` | Cannot read a lab report (F-16) |
| GMO expertise and labelling | GMO labelling check per market: BR (Decreto 4.680/2003, "T" symbol above 1%), US (NBFDS, 5% per ingredient, listed crops presumed BE), EU (1829/2003, 0.9%) | `compliance` row "GMO labelling"; unit tests `test_certifications.py` | GMO status of an ingredient needs supplier records or PCR; refined-ingredient exemptions (US) are only explained, not computed |
| Organic certification | Organic claim rules per market: SisOrg seal (BR), certifier statement (US NOP), EU logo, code number and farming origin (EU); a missing US certifier statement or EU code number is a fail; an organic claim with a declared GMO is a contradiction (XC5) | `compliance` row "Organic claim"; rule XC5 | Logos are only seen when transcribed as text |
| GFSI schemes (BRCGS labelling and allergen management) | Allergen declaration per market, claims consistency (gluten-free, lactose-free, vegan), artwork review as a first pass with escalation | Rules XC1-XC4, `compliance`, review tickets | Format checks (bold, 2 mm letters) need the image (F-02) |
| Traceability and document control (ISO 22000, HACCP) | Tickets carry product, supplier, lot or batch, artwork version and failed checks; every result has a `check_id`, the input hash, the rules version and a hash of the data; every rule's basis, dates and history sit in a versioned register; signed decisions and overrides with reasons in the audit log | `create_review_ticket`, `check_label`, `record_review_decision`, `review.audit`, [rule register](07-rule-register.md) | Not linked to a document or specification system (F-12) |
| Competence and impartiality of the reviewer (ISO/IEC 17065, 17025) | The tool proposes and a named person decides; an approval against the tool is an override with a reason; the override rate is monitored | `requires_sign_off`, `record_review_decision`, `usage_stats` | Reviewer roles and authority are not modelled (needs the customer's quality system) |
| Food fraud | Points the analyst to supplier authenticity checks for ingredient categories often named in fraud reports | Knowledge file (marked TO VERIFY) | No fraud database (F-17) |

## Guidelines the agent now follows (instructions v0.6)
1. **Screening, not certification.** Only an ISO/IEC 17065 body certifies; only an ISO/IEC 17025 lab proves a threshold. The agent never writes that a product is organic, non-GMO, certified or compliant.
2. **Every claim needs evidence.** For each claim on the pack, say which evidence settles it: certificate (body, number, scope, validity), lab report, supplier specification or statement.
3. **Market rules are explicit.** Each check names its regulation, so a reviewer can verify it.
4. **Transcribe seals and symbols as text** ("[seal: SisOrg]", "[symbol: T in yellow triangle]") so the rules can see them.
5. **Traceability.** Ask for product, supplier, lot and artwork version before opening a review ticket.
6. **Document control.** Report the rules version, the data version and the `check_id`, so any result can be reproduced.
7. **Three decisions, not two, and none of them is an approval.** Ready for sign-off (a named reviewer signs), Request evidence (the analyst collects a certificate, lab report or supplier record and runs the check again) or Escalate (a failed check or a contradiction). This mirrors how certification and compliance work: missing evidence is a request, not a non-conformity, and the decision belongs to a competent person.
8. **Fail closed on an unsure reading.** When the label cannot be read reliably, no check runs; when a word is unsure, no check can pass (rule INGEST-GATE).
9. **Every rule cites its register entry.** Legal basis, the date it applies from, how well it was checked and its history live in the [rule register](07-rule-register.md); a basis not yet verified returns review, never pass or fail.

## Measured
Agent evaluation v0.5 (`tests/evidence/agent-eval-v0.5.md`), 4 certification and GMO cases × 3 runs: the agent called the rules every time, asked for the right evidence in 12/12, never stated that a product is certified in 12/12, and took the right decision in 12/12. The first v0.5 run found a defect in the specification (tool and instructions disagreed on when to escalate); the three-decision rule fixed it.

Agent evaluation v0.6 (`tests/evidence/agent-eval-v0.6.md`): the same cases passed 12/12 again with "ready for sign-off" in place of "approve"; the Analyst cases never said the tool approved a label (15/15); unsure readings were declared as such and got no sign-off (9/9); and a reviewer's override was recorded only with a reason (6/6).

## Roadmap items added
| ID | Activity | Why | Priority |
|---|---|---|---|
| F-15 | Look up certificates in public registers (USDA Organic Integrity Database, MAPA CNPO, Non-GMO Project product list) through a tool | Turns "verify the certificate" into a check | P2 |
| F-16 | Read a lab report (PDF) and compare its result with the claim's threshold | Closes the loop on gluten-free, lactose-free and GMO claims | P2 |
| F-17 | Food fraud vulnerability as data (ingredient category → fraud types and sources) | GFSI food fraud requirement | P3 |
| F-18 | Market rules as data for GMO and organic, including the outcome of PLC 34/2015 in Brazil and updates to the USDA BE list | Regulation changes without code changes (with F-09) | P2 |

## Sources
See `agent/knowledge/standards-and-certifications.md`, section Sources.
