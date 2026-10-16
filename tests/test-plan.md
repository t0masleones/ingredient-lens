# Test plan (v0.1)

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
