# 04 - Critical review and roadmap (after v0.4)

A cold look at what was built, what the evidence really shows, and what should come next. Written for the project owner and for anyone deciding whether this prototype deserves engineering time.

## 1. What the evidence shows, and what it does not
| Claim | Evidence | How strong |
|---|---|---|
| The rules engine gives the expected verdict on the golden set | 25/25 text rows | Weak: the golden set was written by the same author and used while building the rules |
| The engine rarely misses a declared allergen on real products | 6,000 products: 25 of 4,607 declared allergens came out 🟢 (0.5%); none of the 25 had the allergen readable in the ingredient text | Medium: large sample of real labels, but the reference allergens are partly derived by Open Food Facts with the same taxonomy this project imports, so agreement is inflated |
| Claims on the pack (vegan, gluten-free, lactose-free) seldom conflict with the engine | Vegan: 30 🔴 of 763 claims; gluten-free: 65 of 1,311; lactose-free: 98 of 260 (mostly milk listed without lactase) | Medium: independent of the rules, but a conflict can be the engine, the data or the label |
| The engine is deterministic, case-insensitive and STRICT is never milder | 94,097 metamorphic checks: 0 failures on those properties; 45 on ingredient order (0.2%) | Strong for these properties; they say nothing about correctness |
| The agent (LLM + tools) answers safely and clearly | None | **Not tested.** No chat run of the golden set, no photo test, no UAT |

The biggest gap is the last line. Everything a user sees goes through the model: transcription from a photo, the decision to call the tool, the wording and the safety rules. None of that has been measured.

## 2. Weaknesses found
### Product and business analysis
- **No user evidence.** Personas and pain points are hypotheses; no interview, no UAT, no adoption data.
- **No business case.** No baseline time per label check, no volume, no ROI. The Analyst workflow (D-07, closest to FoodChain ID's business) is still only "proposed".
- **Scope drift toward consumers.** Shopper and Cook modes are easy to demo but far from B2B value: regulatory first-pass review, supplier specification checks, support tickets about allergens.

### Safety and quality
- **The model layer is unmeasured** (see above). R-04 (model softens the tool verdict) and R-05 (transcription errors) are still only "monitored" by intention.
- **Lexical matching.** The engine finds words; it does not understand them. Known blind spots: negations inside an ingredient ("sem leite"), German compound words without a space ("Vollmilchpulver" is not split into "milch"), ingredient text with typos or OCR noise, quantities written as words.
- **Information outside the ingredient text.** A separate allergen box, a "may contain" line in another part of the pack or the nutrition table are invisible unless the model transcribes them.
- **Regulation is simplified.** US "gluten" stands for wheat (barley is not a major allergen in the US); lactose thresholds cannot be checked from text; Brazilian "contém derivados de" is read as "contains"; the 2025 Anvisa revision (convergence with Codex) is not reflected.
- **Data trust.** 35k terms come from volunteers. The conservative rule prevents false greens from missing data, but a wrong positive fact (an ingredient wrongly marked vegan) would pass. 15 curated rows still lack a source.

### Engineering and operations
- **Local only.** The MCP server runs on one laptop; there is no hosted version, no authentication, no multi-user audit trail.
- **No monitoring of the model's behaviour.** `usage_stats` counts tool calls, but not answers given without a tool call.
- **Data refresh is manual.** No schedule, no diff review step, no version pin of the taxonomy snapshot in the results.

## 3. Roadmap (proposed future activities)
Ordered by value for a regulated B2B setting. P1 = before showing results as evidence; P2 = next iteration; P3 = if the pilot continues.

| ID | Activity | Why | Effort | Priority |
|---|---|---|---|---|
| F-01 | Automated eval of the full agent: run the golden set and 50 benchmark labels through Claude with the MCP tools, grade with rules plus an LLM judge against `must_include` / `must_not` | Measures what users actually see (R-04, R-05) | M | P1 |
| F-02 | Photo test set: 30 label photos with known text; measure transcription accuracy and retake requests | Photo reading is the first failure point | M | P1 |
| F-03 | UAT with 3 people (one per persona) and 5 cases each; record trust and confusion | Validates the problem and the wording | S | P1 |
| F-04 | Reposition on the Analyst workflow: label compliance first pass for BR/US/EU, with a to-be map, volumes and an ROI model (minutes saved × labels per month × share that needs no full review) | Ties the prototype to the B2B business | S | P1 |
| F-05 | Manual review of every benchmark miss and claim conflict; turn each real engine error into a unit test | Converts the benchmark into permanent regression tests | S | P1 |
| F-06 | German compound-word splitting and negation handling ("sem", "without", "ohne") in the matcher | Known blind spots | M | P2 |
| F-07 | Track answers without a tool call (instruction + log field) and alert when the rate rises | Monitoring after go-live | S | P2 |
| F-08 | Scheduled data refresh (GitHub Actions monthly): regenerate `off-terms.csv`, run all tests, open a pull request with the diff for review | Governed data, not a one-off import | S | P2 |
| F-09 | Market rules as data: a versioned table of allergens per market and per regulation, including the outcome of the Anvisa 2025 revision | Regulation changes without code changes | M | P2 |
| F-10 | Source the last 15 curated rows; second reviewer for any curated change (pull request rule) | Data governance (R-02) | S | P2 |
| F-11 | Hosted MCP server (remote, with authentication) so a team can use the same tools and audit log | Needed for a real pilot | L | P3 |
| F-12 | Input from documents: supplier specification sheets (PDF) from a shared folder, batch report for analysts | Closest to the regulatory workflow | L | P3 |
| F-13 | Additional regulated sources when downloadable: FDA Substances Added to Food, Anvisa additive lists | Regulated coverage | M | P3 |

## 4. What went well and should be kept
- Decisions are logged with the alternatives considered; every change has a changelog line and a test.
- Safety rules are enforced in code, not only in the prompt (STRICT mode, "never green without evidence").
- Data has provenance on every row, and imports are scripted, reproducible and credited.
- Tests now run automatically on every push (GitHub Actions), including a benchmark on real products.
