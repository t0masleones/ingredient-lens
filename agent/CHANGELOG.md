# Agent changelog

## v0.6 - 2026-10-17 (instructions v0.6, rules engine 0.6.0)
Retrieval and grounding (RAG practices, after reviewing how the agent uses its knowledge):
- **What was kept.** Facts that decide a verdict stay in deterministic tools (rules engine, ingredient database, rule register); they are not retrieved text. The five knowledge files (about 30 KB) still sit in full in the Claude Project: at this size full context is the recommended choice, and a vector database would add risk, not value.
- **New tool `search_knowledge`.** The knowledge files split into their own sections (39 passages), ranked by BM25 with section titles weighted, a minimum share of the question covered (a single shared word is not an answer), source lists left out, and Portuguese or Spanish domain words expanded to English. Every passage has an id to cite, the file version and a `to_verify` flag. It works where the project files are not in context (Claude Desktop with the server only).
- **Grounding rule in the instructions.** Every fact comes from a tool result and is cited: `rule_id` from `check_label`, exact rows from `lookup_ingredient`, passage ids from `search_knowledge`; if nothing is returned, the agent says the knowledge does not cover it.
- **`lookup_ingredient` labels each row `exact` or `partial`.** A partial row ("sal" matching "salaison", a nonsense phrase matching "ente") is marked as a different term.
- **Retrieval measured.** `tests/test_knowledge_retrieval.py`: recall@3 0.94 on 17 fixed questions in English and Portuguese (one known miss: "gluten statement Brazil" ranks the glossary above the Brazilian rule), an unrelated question returns nothing, CI fails if recall drops. Agent evaluation (`tests/evidence/grounding-check-v0.6.md`): searched the knowledge 9/9, cited the passage 6/6, said "not covered" with no number from memory 3/3. A regression check of the Analyst, gate and safety cases stayed 10/10.

 (`docs/04-critical-review.md`, section 6):
- **Overrides as controlled deviations (F-23).** `record_review_decision` needs a `reason_category` (supplier_evidence, transcription_error, data_error, rule_exception, artwork_pending) for every override, and on a critical finding (allergen, gluten or lactose statement, claim contradiction) also the `evidence` and a `second_reviewer` who is not the reviewer. The tool's own result is kept next to the override.
- **Escalation reasons (F-24).** `usage_stats` reports the top escalation reasons, the reviewer's verdict on each escalation (`escalation_needed`), overrides by category, and a CAPA signal when one category repeats three times.
- **What text cannot settle (F-25).** In Analyst mode `check_label` returns `not_verifiable_from_text`: additive limits, standards of identity, contaminants, packaging and cross-contact controls, each with the evidence it needs. They never change the decision.
- **Answers without the rules (F-07).** New tool `log_answer_without_check`; `usage_stats` reports the count, the rate and the reasons.
- **Monthly data refresh (F-08).** `.github/workflows/data-refresh.yml` regenerates `off-terms.csv`, runs the tests and the golden set, and opens a pull request with the diff for review.
- **Sign-off recheck.** The sign-off cases ran again with the new rules (`tests/evidence/signoff-recheck-v0.6.md`): 9/9; the agent asks for the category, evidence and second approver before recording a critical override.
- **Hard-case test pack (F-27)**, `tests/test_hard_cases.py`: gluten-free with malt or ambiguous starch, vegan with natural flavours or enzymes, may-contain versus contains, umbrella ingredients, statements that contradict the list, additives without concentration, unsure critical words. It found two umbrella terms that came out 🟢 for a soy allergy in STRICT mode: "temperos" (read as a single spice) and "realçador de sabor". Both now carry possible allergens (curated rows; a stricter change, so one reviewer). The benchmark numbers above were measured before this data change.
- Tests: 3,286 passed. Golden set 25/25.

An external AI review of v0.5 scored it 6.5/10 for rigor and 7/10 for business value and named three next steps: an interpretable benchmark, an ingestion gate that fails closed, and governed rules. All three are in this version (`docs/04-critical-review.md`, section 5).
- **Ingestion gate that fails closed (rule INGEST-GATE).** `check_label` takes `source` (photo, text or recipe), `transcription_confidence` and `complete_pack`. Low confidence or no ingredient list: `needs_manual_review`, no check runs. Medium confidence or any word marked [?]: nothing can be 🟢 and no check can pass. A photo of part of the pack: a missing statement is review, not fail.
- **Rule register** (`mcp-server/rules/register.json`, page `docs/07-rule-register.md`). Each rule has its intent, engine behaviour, legal basis per market (citation, link, date it applies from, how well it was checked), history and tests. Every checklist row and mismatch carries `rule_id`, citation and verification level; a basis not yet verified never gives pass or fail. CI fails when a review is overdue, a rule has no test, the page is out of date or the register and engine versions differ.
- **Governance defect fixed:** v0.5 changed rules (GMO, organic, XC5) without raising the rules version, which stayed 0.4.0. A test now makes that impossible.
- **Sign-off instead of approval.** `next_step` "approve" is now `ready_for_sign_off`, and `requires_sign_off` is true in Analyst mode: a named reviewer signs, the tool never approves. New tool `record_review_decision` (approve, reject, approve_with_override): a rejection or an override needs a reason, and approving a label the tool did not mark ready is recorded as an override. `usage_stats` reports decisions, the override rate and the uncertainty rate.
- **Traceability.** Every result has a `check_id` (hash of the input, parameters, rules version and data hash), `input_sha256`, the data version with a SHA-256 of both data files, and `match_sources` per ingredient. The audit log records the check, the gate, each checklist row by rule and the decision.
- **Interpretable benchmark.** Each miss gets a cause from keyword lists independent of the engine (ingestion, parsing, taxonomy, reference definition); extraction rates by input type (text measured, photos not); reference B checked from the ingredients alone; the false-alarm proxy split by whether the allergen is named in the text.
- **Found by the benchmark and fixed:**
  - "CONTÉM GLÚTEN. DERIVADOS DE SOJA" (a statement split by a period) hid the soy declaration.
  - A statement inside an ingredient's parentheses ("arôme naturel (contient alcool)", "vinagre (contém sulfitos)", "coconut flakes (contains: sulfur dioxide)") ended the list. Every ingredient after it was dropped, so gelatin could come out 🟢 for a vegan, and the rest of the list was read as the label's allergen statement: false XC2 mismatches, and a declaration the label does not have. "Contains one or more of the following:" now lists ingredients.
  - An unclosed parenthesis in OCR text ("farinha de trigo (glutenamido de milho, …") put the rest of the label inside one ingredient, so a "Pode conter vestígios de" line was read as ingredients, not traces. Parenthesis depth now counts only pairs that close (found by the ingredient-order property), and a statement word right after an unclosed parenthesis ("(CONTEM OLEO DE SOJA, AGUA, … SORO DE LEITE") stays part of the list.
- **Data governance:** synonym policy, a disputed-mapping workflow (a change that makes a term milder needs a second reviewer) and GitHub issue forms for disputed mappings and rule changes (`mcp-server/data/README.md`).
- Instructions v0.6: scope statement, honest transcription confidence, the gate, rule ids in the checklist, sign-off and overrides, `check_id` in document control.
- Agent evaluation v0.6 (120 runs, 3 per case): 0 "safe" claims; emergency first 21/21; Analyst 15/15, never saying the tool approved a label; certification 12/12; ingestion gate 9/9; sign-off and overrides 6/6. Plain language judged 4+/5 in 8/18; a controlled re-judge of the v0.5 and v0.6 answers found no change (mean 3.87 and 3.85, while the judge's own spread on the same answer is 1.1 points), so US-02 stays partly met. Four grader errors (contractions, "what is safe for you", Portuguese word order) were fixed with control sentences (`mcp-server/tests/test_eval_graders.py`) and all runs graded again.
- Tests: 3,286 passed. Golden set 25/25.

## v0.5 - 2026-10-17 (instructions v0.5, rules engine 0.4.0)
Standards a food certification, testing and compliance company works under, turned into agent behaviour (`docs/06-standards-alignment.md`).
- Screening is not certification: only bodies accredited to ISO/IEC 17065 certify, and only ISO/IEC 17025 laboratories prove thresholds. The agent never writes that a product is certified, organic, non-GMO or compliant; it names the evidence that settles each claim.
- New compliance checks: GMO labelling per market (BR: Decreto 4.680/2003 and the T symbol above 1%; US: bioengineered disclosure, 7 CFR Part 66; EU: Regulation 1829/2003, 0.9%), organic particulars (SisOrg; "Certified organic by …"; EU code number and farming origin; a missing US certifier statement or EU code is a fail), non-GMO claims and other certification marks.
- New cross-check XC5: an organic claim with a declared GMO ingredient.
- Three decisions instead of two: `next_step` is approve, request_evidence (with `evidence_needed`) or escalate. Found by the agent evaluation: the tool and the instructions disagreed on when to escalate, and the model followed one or the other.
- Traceability in review tickets: market, product, supplier, lot or batch, artwork version and failed checks; tickets name the rules and data version.
- New knowledge file `standards-and-certifications.md`; seals and symbols are transcribed as text ("[seal: SisOrg]", "[symbol: T in yellow triangle]").
- Agent evaluation v0.5 (105 runs, 3 per case): never "safe" 105/105, emergency first 21/21, Analyst 15/15, certification and GMO cases 12/12, plain language judged 4+/5 in 14/18 (partly met; the score varied between 11 and 15 of 18 across three runs).
- Tests: 3,145 passed. Golden set 25/25.

## v0.4.1 - 2026-10-17 (instructions v0.4, rules engine 0.4.0)
- D-07 done: the Analyst workflow (label compliance first pass) is the primary use case. Instructions v0.4 put it first, with a new Analyst format (compliance checklist, allergens found vs declared, escalation, handoff note, supplier questions). A label shared with no personal restriction goes to Analyst mode.
- `check_label` returns `compliance`: per market (BR, US, EU), each check with pass / fail / review / n/a and its legal basis (US-18). Points text cannot settle (format, amounts, bold emphasis) are always "review".
- US-08: new section 0 "Emergency first". `check_label` returns `"verdict": "urgent"` when symptoms are described (PT, EN, ES), with emergency numbers and no analysis; no false trigger on the 6,000 benchmark labels.
- US-07: every result carries `wording`, the sentence to use instead of "safe"; the instructions list the forbidden phrases in both languages and what to say when the user insists.
- US-02: plain-language rules (12-year-old reader, every code explained, no regulatory asides in Shopper and Cook) and a new knowledge file, `plain-words-glossary.md`.
- First automated evaluation of the full agent (`tests/agent_eval/`): 93 runs of Claude with the instructions, knowledge files and MCP tools. Never "safe": 0 in 93. Emergency first: 21/21 (no false emergency 3/3). Analyst escalation: 15/15. Plain language: objective checks 18/18, model judges 4+/5 in 11/18 and 9/18, so US-02 is partly met (F-14). See `tests/evidence/agent-eval-v0.4.md`.
- Tests: 3,127 passed. Golden set 25/25.

## v0.4 - 2026-10-16 (rules engine 0.4.0, data, tests at scale)
- Knowledge: Open Food Facts import now reads the source taxonomies with synonyms, adds French, German, Italian and Dutch, and uses the taxonomy's own allergen property: 10,902 → 35,043 terms (653 curated terms win over them). A foreign word never replaces a Portuguese, English or Spanish one.
- EU allergens (backlog 12): celery, mustard, sulphites and lupin are now allergen groups, with curated terms citing Regulation 1169/2011 Annex II. Before, "aipo" and "mostarda" were in the data without an allergen, so they came out 🟢 for an allergic user.
- Market rules: XC2 (allergen missing from the statement) checks only the allergens each market requires (BR: RDC 26/2015, no sesame or molluscs; US: FALCPA + FASTER Act; EU: all 14). Other allergens become a note.
- EU labels: "Zutaten", "Ingrédients", "Ingredienti", "Ingrediënten"; "peut contenir", "kann Spuren … enthalten", "può contenere"; "sans gluten", "glutenfrei"; German case endings ("Haselnüssen").
- Market rule: oats are 🟡 for gluten in the US (not a gluten grain under 21 CFR 101.91) and stay 🔴 in BR, the EU and STRICT mode; a US "gluten free" claim with oats is no longer a mismatch.
- Found by the benchmark on real labels and fixed: a period inside parentheses or used as a separator ended the list (milk and soy after it were dropped); French trace wording ("Peut aussi contenir", "Traces éventuelles de"); unnamed oil now possible soy; decimal commas; German ß; Open Food Facts `_allergen_` markup; "corn semolina" no longer inherits gluten. Also: claims printed before the list ("Sem glúten, Rico em fibras, Farinha de trigo…", "CONTÉM FENILALANINA Água…") emptied the ingredient list. Only the claim words are now moved to the statements; "fat free milk" and "SEM GLÚTEN Leite integral" keep their ingredient.
- Data governance (backlog 5): 64 of the 83 unsourced curated rows confirmed against Open Food Facts, 4 more cite a regulation, 15 left for a person (`tests/evidence/curated-crosscheck.md`). The check also found two import bugs: peanuts tagged as tree nuts, molluscs as crustaceans.
- Knowledge: additive class names (Codex CXG 36-1989) and vitamin forms (EU 1925/2006), with the right caution ("emulsificante" may be soy or egg, "corante" may be carmine).
- Tests: 3,108 passed (108 unit and data tests, 3,000 property checks on 1,500 real products). Golden set 25/25. GitHub Actions runs them on every push.
- Benchmark on 6,000 real products (BR, US, FR, DE; 160,570 engine runs): 25 of 4,607 declared allergens missed (0.5%); manual review found none where the allergen was readable in the ingredient text (`tests/evidence/benchmark-review-v0.4.md`). Coverage 91.5-95.0%. Metamorphic properties: 94,097 checks, 45 failures (ingredient order, under review).

## v0.3 - 2026-10-16 (rules engine 0.3.0, data and label rules)
- Data: 10,902 terms from the Open Food Facts taxonomies (ODbL) in `mcp-server/data/off-terms.csv`, generated by `data/import_off.py`. Portuguese, English and Spanish names, and additive codes as both E and INS numbers. The 430 curated terms still win. See `mcp-server/data/README.md`.
  - Safety rule: Open Food Facts gives diet status only. An allergen is ruled out only with evidence (vegan ingredient, or fruit, vegetable, herb, spice, salt, water); otherwise it is flagged as possible (🟡).
  - Coverage on 10 new, untuned labels (5 BR, 5 US): 75% → 95% of ingredients found.
- Fix: the curated data and the origin glossary said gelatin was E441. E441 / INS 441 is a rapeseed-oil emulsifier; gelatin has no additive number.
- Label rules v0.2: US items checked against the FDA (9 major allergens, Edition 5 guidance with coconut removed from tree nuts, 21 CFR 101.91 gluten-free) and EU items against Regulations 1169/2011 and 828/2014. Brazil: noted that RDC 727/2022 consolidated the allergen and lactose rules.
- Engine: `vegetarian` treats "maybe from slaughter" as 🟡; results show `data_version` (curated + imported) and the data license; the server no longer keeps the database file locked, so it can be rebuilt while Claude Desktop is open.
- Instructions v0.3: explain the "allergens not verified (Open Food Facts term)" note.
- Tests: 50 passed (new `tests/test_open_food_facts.py`). Golden set (text rows): 25/25.

## v0.2.1 - 2026-10-16 (rules engine only)
Code review fixes, each with a test in `mcp-server/tests/test_review_findings.py` (written first, failing on v0.2.0).
- Safety: items after "contains 2% or less of:" / "contém menos de 2% de:" were dropped, so gelatin or carmine could come out 🟢 for a vegan. They are now read as ingredients.
- Safety: the word "vegan"/"vegano" inside an ingredient ("vegan butter", "queijo vegano") ended the list. Claims now end the list only when they stand alone.
- Without an "INGREDIENTES:" header, "Pode conter leite" was read as an ingredient (🔴). It is now a may-contain statement (🟡).
- "(65%)" and "(INS 322)" are no longer counted as unknown ingredients.
- New terms (`v0.2.1-added`, no cited source yet): vegan butter/cheese/mayonnaise and the Portuguese names, cashew cheese, queijo de castanha, coconut cream, mayonnaise and maionese (egg).
- `create_review_ticket`: reports the real destination, and keeps the case in the local queue when GitHub fails or there is no token.
- `eval_rules.py` no longer crashes on Windows when its output is redirected.
- Tests: 27 passed. Golden set (text rows): still 25/25.

## v0.2 - 2026-10-16
- Added the `mcp-server/`: the agent now calls tools instead of classifying from memory.
  - `check_label`: deterministic rules engine (ingredient matching, profile, STRICT mode, cross-checks XC1-XC4).
  - `lookup_ingredient`: SQLite ingredient database built from `mcp-server/data/ingredients.csv` (glossaries turned into data, each row with its source).
  - `create_review_ticket`: human-review queue (GitHub Issues or a local file).
  - `usage_stats`: metrics from the audit log (verdict mix, escalation rate, mismatch rules).
- Instructions: new "Tools" section. The rules engine decides; the model transcribes and explains.
- Rules engine vs golden set (text rows): 25/25 after one fix (T04: a zero-lactose claim with lactase settles the "contains milk" declaration for lactose intolerance). See `tests/evidence/results-rules-v0.2.md`.
- Known gap: rows marked `v0.2-added` in the CSV are common ingredients added without a cited source; review them. The golden set was used while building the rules, so add new unseen cases before claiming accuracy.

## v0.1 - 2026-10-16
- First version: Shopper, Cook and Analyst modes; allergen/intolerance classification; animal vs plant origin; label cross-check.
- Knowledge files: lactose and gluten glossary, origin glossary, label rules (Brazil items checked against sources; US and EU items still to verify).

## Next
- Photo test set with known text (F-02): measure transcription, the confidence the agent declares and the ingestion gate on real photos.
- Hand-labelled reference set (F-19): a confusion matrix per check, market and input type.
- Decide the candidate disputed mappings found by the v0.6 benchmark (`tests/evidence/benchmark-review-v0.6.md`); each needs a second reviewer because it makes a term milder.
