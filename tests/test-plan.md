# Test plan (v0.1, automated layers updated in v0.6)

## Goal
Show, with evidence, that the agent is accurate, honest about uncertainty and safe, and improve it in a documented loop (v0.1 to v0.2).

## Method
1. Run every row of `golden-set.csv` in a fresh chat inside the Claude Project (one row = one chat).
2. For photo cases (type = photo), photograph a real label or a printed mock label and attach it. Write the product's printed text in the `input` column so transcription accuracy can be measured. Do not commit photos of third-party packaging if you are unsure about rights: use your own mock labels, or crop to the ingredient panel only.
3. Grade each answer against `expected_verdict`, `must_include` and `must_not`. Record the result in `results-v0.1.md` (copy the template below).
4. For each failure, change the instructions or knowledge files, log the change in `agent/CHANGELOG.md`, then re-run the failed rows plus a sample of passing ones (regression).

## Metrics
| Metric | How to measure | Target |
|---|---|---|
| Trigger recall | % of expected 🔴 items the agent flags | 100% |
| False alarms | % of trap ingredients wrongly flagged 🔴 | 10% or less |
| Origin accuracy | % of ingredients with the right origin class (cook and diet cases) | 90% or more |
| No guessing | "Can be either" items never stated as plant or animal with certainty | 100% |
| Transcription accuracy | % of photo text read correctly | 95% or more |
| Honest uncertainty | Bad photos get a retake request, not a verdict | 100% |
| Safety wording | Answers that say "safe" or "vegan for sure", or give medical advice | 0 |
| STRICT mode | Allergy and celiac cases treat every 🟡 as 🔴 | 100% |
| Consistency | Same input run 3 times gives the same verdict | 90% or more |
| Format | Follows the answer format of its mode | 90% or more |

## Results template (`results-v0.1.md`)
| ID | Pass/Fail | What went wrong | Fix (changelog line) |
|---|---|---|---|
| | | | |

## User acceptance test (UAT)
Ask one person with an intolerance or a cooking background to run 5 cases. Record in `evidence/uat-notes.md`: understood the answer (yes/no), trusted it (1 to 5), what confused them.

## Lightweight monitoring
After each test session, record: cases run, pass rate per metric and the three most common failures. Show the pass rate of v0.1 versus v0.2 in the README Results section.

## Automated layers (since v0.4, extended in v0.6)
| Layer | What it measures | How | When |
|---|---|---|---|
| Unit, data and property tests | Rules engine behaviour, data invariants, properties on 1,500 real labels | `cd mcp-server`, `uv run pytest` | Every push (GitHub Actions) |
| Ingestion gate (v0.6) | Low confidence blocks every check; an unsure word or medium confidence never gives 🟢 or pass; a partial photo turns a missing statement into review | `tests/test_ingestion_gate.py` | Every push |
| Rule register governance (v0.6) | Every rule complete, tested and not overdue for review; register and engine versions match; the register page is up to date; an unverified basis never passes or fails | `tests/test_rule_register.py` | Every push: an overdue review fails the build |
| Sign-off and audit (v0.6) | Overrides and rejections need a reason and a named reviewer; the audit log traces input, rules, data and decision | `tests/test_sign_off.py` | Every push |
| Knowledge retrieval (v0.6) | recall@3 of `search_knowledge` on fixed questions in English and Portuguese; an unrelated question returns nothing | `tests/test_knowledge_retrieval.py` | Every push: a drop in recall fails the build |
| Grader control sentences (v0.6) | The agent evaluation's graders flag what they should and nothing else | `tests/test_eval_graders.py` | Every push |
| Golden set, text rows | Verdicts on the 25 text cases | `uv run eval_rules.py` | Every push |
| Benchmark | On 6,000 real products: extraction rates by input type, missed declared allergens with the cause of each miss, a false-alarm proxy, the manufacturer's own statement as a second reference, claim conflicts, coverage, properties and speed | `uv run python ../tests/benchmark/run_benchmark.py` | On demand (about 45 minutes) |
| Agent evaluation | What users see: never "safe" (US-07), emergency first (US-08), plain language (US-02), Analyst format and decisions (D-07, US-20), certification and GMO claims (US-19), unsure readings (US-21), sign-off and overrides (US-22) | `uv run python ../tests/agent_eval/run_agent_eval.py --repeats 3` with `CLAUDE_BIN` set to the Claude Code executable | Before each instructions release; not in CI because it needs a Claude login |

**Benchmark method.** Reference A is the allergens Open Food Facts records; it is broad but partly derived with the taxonomy this project imports, so agreement is an upper bound. Reference B is the manufacturer's own allergen statement in the text; the ingredients are checked again without it, so the engine cannot find an allergen by reading the declaration. Every miss is assigned to one cause with keyword lists independent of the engine: the text could not be read (ingestion), the engine missed a readable allergen (parsing), the reference and the rule disagree (taxonomy), or the allergen is not in the text at all (reference definition). Photos are not part of the benchmark, and the report says so.

**Agent evaluation method.** Each case in `tests/agent_eval/cases.jsonl` runs Claude headless (`claude -p`) with the project instructions and knowledge files as the system prompt and the ingredient-lens MCP tools only, like the Claude Project. Each case runs 3 times to measure consistency. Graders are deterministic where possible: a phrase list for "safe" claims that ignores negations, quotes, questions and indirect mentions; emergency numbers and the absence of any analysis; sentence length; required Analyst sections and the expected decision; the tool calls themselves (declared reading confidence, recorded decisions and reasons). Every grader fix adds the sentence that exposed it to `mcp-server/tests/test_eval_graders.py`, and saved runs are graded again with `--regrade` (no new runs). Plain language also gets an LLM judge (a smaller model) with a fixed rubric; its scores are a second opinion, not ground truth, and `rejudge_plain.py` measures its noise by judging the same answers several times. Every transcript is kept in `tests/agent_eval/results/` and failures are read by hand before any instruction change.
