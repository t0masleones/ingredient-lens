# Grounding check (instructions v0.6 with search_knowledge, model sonnet, judge haiku)

9 agent runs on 2026-10-17. Each run: Claude headless with the project instructions and knowledge files as the system prompt and the ingredient-lens MCP tools. Raw transcripts: `tests/agent_eval/results/runs-20261017T185557Z.jsonl`. Usage-equivalent cost: $0.43.

| Story | Runs | Runs passing every check | Check | Passed |
|---|---|---|---|---|
| GROUND | 9 | 9/9 | searched the knowledge files | 9/9 |
|  |  |  | cites a passage id | 6/6 |
|  |  |  | says the knowledge does not cover it | 3/3 |
|  |  |  | gives no number from memory | 3/3 |

## Failures

None.

## Example answers
