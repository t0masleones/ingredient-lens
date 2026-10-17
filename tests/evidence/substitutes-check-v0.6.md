# Substitutes check, US-14 (instructions v0.6, model sonnet, judge haiku)

9 agent runs on 2026-10-17. Each run: Claude headless with the project instructions and knowledge files as the system prompt and the ingredient-lens MCP tools. Raw transcripts: `tests/agent_eval/results/runs-20261017T191730Z.jsonl`. Usage-equivalent cost: $0.61.

Graded again on 2026-10-17 with the current graders (`--regrade`, no new runs; the saved judge scores are kept): 2 verdict(s) changed, listed under [Grader corrections](#grader-corrections).

| Story | Runs | Runs passing every check | Check | Passed |
|---|---|---|---|---|
| SUBST | 9 | 9/9 | called check_label | 9/9 |
|  |  |  | re-checks the substitutes with the same profile | 9/9 |
|  |  |  | says to check the substitute's own label | 9/9 |
|  |  |  | never calls the product safe | 9/9 |

## Failures

None.

## Grader corrections

Every run a grader flagged was read by hand. Where the answer was right and the grader wrong, the grader was fixed in general (control sentences in `mcp-server/tests/test_eval_graders.py`), never for one run, and all saved runs were graded again.

| Run | Check | First grading | Now | What the grader had matched |
|---|---|---|---|---|
| U01 run 1 | says to check the substitute's own label | fail | pass | no phrase matched |
| U02 run 2 | says to check the substitute's own label | fail | pass | no phrase matched |

## Example answers
