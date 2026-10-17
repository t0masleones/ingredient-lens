# 04 - Critical review and roadmap (updated after v0.6)

A cold look at what was built, what the evidence really shows, and what should come next. Written for the project owner and for anyone deciding whether this prototype deserves engineering time. Section 5 answers an external review of v0.5, point by point.

## 1. What the evidence shows, and what it does not
| Claim | Evidence | How strong |
|---|---|---|
| The rules engine gives the expected verdict on the golden set | 25/25 text rows | Weak: the golden set was written by the same author and used while building the rules |
| The engine rarely misses a declared allergen on real products | 6,000 products: 22 of 4,607 declared allergens came out 🟢 (0.5%); 20 of them are not in the ingredient text, 2 are rule disagreements, 0 are engine errors. "Detected" includes 492 🟡 (10.7%), a flag for a person rather than a finding | Medium: a large sample of real labels, but reference A is partly derived with the taxonomy this project imports, so agreement is inflated |
| The engine finds what manufacturers declare, without reading the declaration | With the statement removed, 1,176 of 1,191 declared allergens (98.7%) are still flagged from the ingredients, 933 of them 🔴; 91.3% of the definite flags are also declared | Medium: independent of the taxonomy, but only for the products whose text includes a statement, and a declaration can include cross-contact |
| The engine's definite flags are rarely false alarms | 3,039 🔴 for an allergen the reference does not record: 2,841 (93.5%) name the allergen in the text, so the reference is incomplete; the other 198 (0.25% of product–allergen pairs) are an upper bound, and most were correct when read by hand | Medium: an upper bound, read by hand on a sample; no hand-labelled ground truth yet (F-19) |
| Claims on the pack (vegan, gluten-free, lactose-free) seldom conflict with the engine | Vegan: 30 🔴 of 763 claims; gluten-free: 65 of 1,311; lactose-free: 98 of 260 (mostly milk listed without lactase) | Medium: independent of the rules, but a conflict can be the engine, the data or the label |
| The engine is deterministic, case-insensitive and STRICT is never milder | 94,153 metamorphic checks: 0 failures on those properties; 32 on ingredient order (0.2%) | Strong for these properties; they say nothing about correctness |
| An unsure reading never becomes a pass | 11 unit tests on the gate; agent evaluation: 9/9 unsure readings declared and stopped | Strong in code; **weak in practice** until real photos calibrate the confidence the model declares (R-12) |
| The agent (LLM + tools) answers safely and clearly | 120 headless runs (v0.6): 0 "safe" claims, emergency first 21/21, Analyst 15/15, certification 12/12, sign-off 6/6; plain language 4+/5 in 8 of 18 runs | **Partly tested.** Text only, headless instead of the project UI, graded by rules and a model judge, not by users. No UAT |

The biggest gap is still the input. Rules, data and safety wording are measured at scale; photo transcription, the default Shopper format's readability and real users' trust are not.

## 2. Weaknesses found
### Product and business analysis
- **No user evidence.** Personas and pain points are hypotheses; no interview, no UAT, no adoption data.
- **No measured business case.** The ROI model ([05](05-analyst-workflow.md)) is ready, but every input except the model cost is an assumption until a pilot.
- **Scope drift toward consumers** is contained: the Analyst workflow is primary since v0.4, and v0.6 states what is in and out of scope.

### Safety and quality
- **The input is the weakest link.** The ingestion gate fails closed, but it relies on the confidence the model declares about its own reading. Without photos with known text, nobody knows how often the model says "high" on a misread (R-12).
- **Lexical matching.** The engine finds words; it does not understand them. Known blind spots: negations inside an ingredient ("non-dairy", "sem leite"), German compound words, typos and OCR noise. The v0.6 benchmark found another parsing defect of the same family (a statement inside parentheses ended the list); each one found becomes a test, but the family is not closed (R-15).
- **Information outside the ingredient text.** A separate allergen box or a "may contain" line elsewhere on the pack is invisible unless the model transcribes it; the open data rarely includes them (statements appear in about 20% of product texts).
- **Regulation is simplified.** US "gluten" stands for wheat; lactose thresholds cannot be checked from text; the 2025 Anvisa revision is not reflected; effective dates are recorded but not applied (R-14).
- **Data trust.** 35,043 terms come from volunteers. The conservative rule prevents false greens from missing data, but wrong positive facts exist: the v0.6 benchmark found soy flour carrying gluten and the Dutch "room" (cream) matching the English word. They wait for a second reviewer (D-19).

### Engineering and operations
- **Local only.** The MCP server runs on one laptop; no hosted version, no authentication, no multi-user audit trail.
- **Monitoring is partial.** `usage_stats` now reports decisions, the override rate and the uncertainty rate, but not answers given without a tool call (F-07).
- **Data refresh is manual.** The data hash makes every result traceable to a data version, but there is no scheduled refresh with a reviewed diff (F-08).

## 3. Roadmap (proposed future activities)
Ordered by value for a regulated B2B setting. P1 = before showing results as evidence; P2 = next iteration; P3 = if the pilot continues.

| ID | Activity | Why | Effort | Priority |
|---|---|---|---|---|
| F-01 | Automated evaluation of the full agent. 120 runs on eight stories in v0.6; next: the golden set T and V cases, and ticket creation end to end | Measures what users actually see (R-04) | M | P1 |
| F-02 | Photo test set: 30 label photos with known text; measure transcription, the confidence the agent declares and the gate's decisions | Photo reading is the first failure point (R-05, R-12) | M | P1 |
| F-03 | UAT with 3 people (one per persona) and 5 cases each; record trust and confusion | Validates the problem and the wording | S | P1 |
| F-04 | Analyst workflow pilot on 50 real labels with a reviewer's decisions, to fill the ROI inputs and measure the override rate | Ties the prototype to the B2B business | S | P1 |
| F-05 | Review every benchmark miss, claim conflict and candidate disputed mapping; each real engine error becomes a test | Converts the benchmark into regression tests and governed data | S | P1 |
| F-06 | German compound-word splitting and negation handling ("non-dairy", "sem", "ohne") in the matcher | Known blind spots | M | P2 |
| F-07 | Track answers without a tool call (instruction + log field) and alert when the rate rises | Monitoring after go-live | S | P2 |
| F-08 | Scheduled data refresh (monthly): regenerate `off-terms.csv`, run all tests, open a pull request with the diff | Governed data, not a one-off import | S | P2 |
| F-09 | Market thresholds and allergen lists as data. The basis, dates and history are in the rule register since v0.6; the thresholds are still in code | Regulation changes without code changes | M | P2 |
| F-10 | Source the last 15 curated rows; second reviewer for any curated change | Data governance (R-02) | S | P2 |
| F-11 | Hosted MCP server (remote, with authentication) so a team shares the tools and the audit log | Needed for a real pilot | L | P3 |
| F-12 | Input from documents: supplier specification sheets (PDF) from a shared folder, batch report | Closest to the regulatory workflow | L | P3 |
| F-13 | Additional regulated sources when downloadable: FDA Substances Added to Food, Anvisa additive lists | Regulated coverage | M | P3 |
| F-14 | "Simple first" Shopper format (verdict, three bullets, next step; details on request), validated with low-literacy users | US-02 is only partly met | S | P1 |
| F-15 | Look up certificates in public registers (USDA Organic Integrity Database, MAPA CNPO, Non-GMO Project list) through a tool | Turns "verify the certificate" into a check | M | P2 |
| F-16 | Read a lab report (PDF) and compare its result with the claim's threshold | Closes the loop on gluten-free, lactose-free and GMO claims | M | P2 |
| F-17 | Food fraud vulnerability as data (ingredient category → fraud types and sources) | GFSI food fraud requirement | M | P3 |
| F-18 | GMO and organic rules as data, including the outcome of PLC 34/2015 in Brazil and USDA BE list updates | Regulation changes without code changes (with F-09) | S | P2 |
| F-19 | Hand-labelled reference set (labels read by a regulatory reviewer): a confusion matrix per check, market and input type | The only way to measure precision and recall without a coupled reference | M | P1 |
| F-22 | Apply effective dates: check a label against the rules in force when it was printed | Jurisdiction and date drift (R-14) | M | P2 |

## 4. What went well and should be kept
- Decisions are logged with the alternatives considered; every change has a changelog line and a test.
- Safety rules are enforced in code, not only in the prompt: STRICT mode, "never green without evidence", the emergency path, and since v0.6 the ingestion gate.
- Rules and data are traceable: every result names the rule, its basis, the rules version and a hash of the data, and the build fails when a rule's review is overdue.
- Measurement explains itself: every miss has a cause, and the benchmark found real defects that a summary number had hidden.
- Tests run automatically on every push, including the evaluation graders' control sentences.

## 5. External review of v0.5 and the response
In October 2026 an external AI review read the public repository at v0.5 and assessed it as a candidate tool for a regulatory team. It scored the work **6.5/10 for rigor** and **7/10 for business value**. It found strong: the boundary between the model and a deterministic engine, the review queue and audit log, the test suite and the safety posture. It proposed three next steps: an interpretable benchmark, an ingestion confidence gate that fails closed, and governance of rules and data as a product (versions, effective dates, tests, change logs). v0.6 is the response. The scores are the reviewer's, at v0.5; they were not re-scored.

### Point by point
| Point raised | What v0.6 does | Evidence | Status |
|---|---|---|---|
| "25 of 4,607 … none readable" reads like a pipeline failure | Every miss gets one cause, from keyword lists independent of the engine: ingestion, parsing, taxonomy or reference definition | 22 misses: 20 not in the text, 2 rule disagreements, 0 engine errors, 0 unreadable texts ([benchmark §3](../tests/evidence/benchmark-rules-v0.6.md), [review](../tests/evidence/benchmark-review-v0.6.md)) | ✅ Done |
| Photo ingestion is unproven | A gate that fails closed: low confidence gives no verdict, an unsure word means nothing passes, part of the pack turns missing statements into review. Extraction is reported by input type, and photos are reported as not measured | `test_ingestion_gate.py` (11 tests); agent evaluation GATE 9/9; [benchmark §1](../tests/evidence/benchmark-rules-v0.6.md) | 🟡 Partial: built and tested, not measured on photos (F-02) |
| Open Food Facts governance | Data versioned by hash in every result; `match_sources` per ingredient; synonym policy; disputed-mapping workflow with an issue form; a milder change needs a second reviewer | [Data governance](../mcp-server/data/README.md#governance); candidates in the [benchmark review](../tests/evidence/benchmark-review-v0.6.md) | 🟡 Partial: process in place, refresh not scheduled (F-08) |
| Taxonomy coupling of the benchmark | Reference B, the manufacturer's own statement, checked from the ingredients alone; false alarms split by an independent keyword list | [Benchmark §4–5](../tests/evidence/benchmark-rules-v0.6.md) | 🟡 Partial: no hand-labelled set yet (F-19) |
| Risk: OCR false negatives | The gate, [?] marks that force the cautious mode, and an instruction that a dropped word is the most dangerous error | Unit tests; agent evaluation | 🟡 Mitigated, not measured |
| Risk: vegan inference from text | Scope statement: the origin of an ambiguous ingredient is out of scope without a supplier declaration; such ingredients stay "can be either" | Instructions v0.6; `test_open_food_facts.py` | ✅ Done |
| Risk: jurisdiction and effective-date drift | Rule register: market, citation, link, date it applies from, verification level, history, tests and a review date per rule; CI fails when a review is overdue | [07 · Rule register](07-rule-register.md); `test_rule_register.py` | 🟡 Partial: dates recorded, not applied (F-22) |
| Risk: automation bias | The tool never approves: "ready for sign-off"; a named reviewer signs; an override needs a reason; the override rate is reported | `test_sign_off.py`; agent evaluation SIGNOFF 6/6 | ✅ Done; needs a pilot to monitor |
| Risk: audit defensibility | `check_id` (hash of input, parameters, rules version and data hash), input hash, rule per checklist row, signed decisions in the audit log | `test_ingestion_gate.py`, `test_sign_off.py` | ✅ Done |
| Need: validated ingestion metrics and a hard "cannot reliably read" state | `needs_manual_review` with no checks run; extraction rates for text | Unit tests; benchmark §1 | 🟡 Partial: the state is built; photo metrics need F-02 |
| Need: rule governance (jurisdiction, citation, effective date, intent, version history) | The register, read by the engine and rendered as a page, with a release process and an issue form | [07 · Rule register](07-rule-register.md) | ✅ Done |
| Need: a clear scope statement | In the instructions, the requirements and the README | [03 · Requirements](03-requirements.md) | ✅ Done |
| Need: confusion matrices per check, country and input type | Allergen detection per market against two references, with precision against the manufacturer's statement; text only | [Benchmark §2 and §5](../tests/evidence/benchmark-rules-v0.6.md) | 🟡 Partial: needs a hand-labelled set and photos (F-19, F-02) |
| Need: controlled-vocabulary governance | Synonym policy and the disputed-mapping workflow | [Data governance](../mcp-server/data/README.md#governance) | 🟡 Partial |
| Need: workflow controls (sign-off, override reasons, uncertainty reporting) | `record_review_decision`; uncertainty and override rates in `usage_stats` | `test_sign_off.py` | ✅ Done |

### The reviewer's question
*"In the 6,000-product set, what percentage of cases did the system confidently extract the ingredient list and the allergen and gluten statements, split by photo, text and recipe?"*

| Input type | Cases | Ingredient list extracted | Allergen statement found | Gluten statement found (Brazil, where it is mandatory) |
|---|---|---|---|---|
| Text | 6,000 product texts | 5,993 (99.9%) | 1,138 of 5,993 (19.0%) | 538 of 1,995 (27.0%) |
| Recipe | 10 golden cases | 10 of 10, judged as expected | n/a | n/a |
| Photo | 0 | **not measured** | **not measured** | **not measured** |

Two cautions. First, a statement "not found" in this data usually means the open database stored only the ingredient list, not that the pack lacks the statement; it says little about the engine. Second, for text the engine does not report a confidence: the confidence belongs to the transcription, so it can only be measured with photos, which is the first item on the roadmap (F-02).

### What did not change
- Photos, users and a hand-labelled reference are still missing; these are the three things that would move rigor most (F-02, F-03, F-19).
- The agent is evaluated headless with the same instructions and tools, not inside the project UI.
