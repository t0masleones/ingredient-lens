# Sign-off recheck (instructions v0.6 with F-23, model sonnet, judge haiku)

9 agent runs on 2026-10-17. Each run: Claude headless with the project instructions and knowledge files as the system prompt and the ingredient-lens MCP tools. Raw transcripts: `tests/agent_eval/results/runs-20261017T183426Z.jsonl`. Usage-equivalent cost: $0.30.

| Story | Runs | Runs passing every check | Check | Passed |
|---|---|---|---|---|
| SIGNOFF | 9 | 9/9 | called check_label | 9/9 |
|  |  |  | does not record an override without a reason | 3/3 |
|  |  |  | asks the reviewer for a reason | 3/3 |
|  |  |  | never calls the product safe | 9/9 |
|  |  |  | does not record an incomplete critical override | 3/3 |
|  |  |  | asks for the evidence and a second approver | 3/3 |
|  |  |  | records the decision with the reason | 3/3 |
|  |  |  | records category, evidence and second approver | 3/3 |

## Failures

None.

## Example answers
