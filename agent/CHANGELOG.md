# Agent changelog

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
- Run the golden set in the Claude chat with the tools connected (`tests/test-plan.md`). For every failure, add one line here with the test ID and the change made.
- Add 10 unseen test cases (held-out set) to check the rules were not tuned to the golden set.
