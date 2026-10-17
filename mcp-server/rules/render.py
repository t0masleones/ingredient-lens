"""Render the rule register (register.json) as the page reviewers read: docs/07-rule-register.md.

The page is generated, never edited by hand. From mcp-server:
    uv run python rules/render.py
tests/test_rule_register.py fails when the committed page differs from the register, so the two cannot drift.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTER = HERE / "register.json"
PAGE = HERE.parents[1] / "docs" / "07-rule-register.md"
TESTS = "../mcp-server/tests/"
LEVEL = {"primary": "✅ Primary", "secondary": "🟡 Secondary", "unverified": "⚪ Unverified", "n/a": "n/a"}
TYPE = {"compliance": "Compliance check", "cross_check": "Cross-check", "safety": "Safety rule"}


def add_months(day: dt.date, months: int) -> dt.date:
    y, m = divmod(day.month - 1 + months, 12)
    return dt.date(day.year + y, m + 1, min(day.day, 28))


def next_review(rule: dict) -> dt.date:
    return add_months(dt.date.fromisoformat(rule["last_reviewed"]), rule["review_every_months"])


def cell(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ")


def basis_summary(rule: dict) -> str:
    marks = {"primary": "✅", "secondary": "🟡", "unverified": "⚪", "n/a": "n/a"}
    parts = [f'{"All" if a["market"] == "ALL" else a["market"]} {marks[a["content_verified"]]}' for a in rule["applies"]]
    return " · ".join(parts)


def rule_section(rule: dict) -> list[str]:
    due = next_review(rule)
    lines = [f'### {rule["id"]}', "",
             f'**{rule["check"]}** · {TYPE[rule["type"]]} · since {rule["since"]} · last reviewed {rule["last_reviewed"]} '
             f'· next review {due} (every {rule["review_every_months"]} months)', "",
             f'**Intent.** {rule["intent"]}', "",
             f'**What the engine does.** {rule["engine_behaviour"]}', "",
             "| Market | Legal basis | Basis checked | Applies from | Date checked | Note |",
             "|---|---|---|---|---|---|"]
    for a in rule["applies"]:
        basis = f'[{cell(a["citation"])}]({a["url"]})' if a["url"] else cell(a["citation"])
        when = a["effective_from"] or "—"
        lines.append(f'| {"All markets" if a["market"] == "ALL" else a["market"]} | {basis} | '
                     f'{LEVEL[a["content_verified"]]} | {when} | '
                     f'{LEVEL[a["effective_source"]] if a["effective_from"] else "—"} | {cell(a.get("note", ""))} |')
    history = " · ".join(f'**{h["version"]}** {h["change"]}' for h in rule["history"])
    by_file: dict[str, list[str]] = {}
    for ref in rule["tests"]:
        file, _, name = ref.partition("::")
        by_file.setdefault(file, []).append(f"`{name}`")
    tests = "; ".join(f"[{file}]({TESTS}{file}): {', '.join(names)}" for file, names in by_file.items())
    return lines + ["", f"**History.** {history}", "", f"**Tests.** {tests}", ""]


def render(register: dict) -> str:
    rules, policy = register["rules"], register["policy"]
    counts = {t: sum(r["type"] == t for r in rules) for t in TYPE}
    unverified = [f'{r["id"]} ({", ".join(a["market"] for a in r["applies"] if a["content_verified"] == "unverified")})'
                  for r in rules if any(a["content_verified"] == "unverified" for a in r["applies"])]
    first_due = min(next_review(r) for r in rules)
    out = [
        "# 07 - Rule register", "",
        "> [!NOTE]",
        "> Generated from [`register.json`](../mcp-server/rules/register.json) by "
        "[`render.py`](../mcp-server/rules/render.py). Do not edit this page: change the register, run "
        "`uv run python rules/render.py` from `mcp-server`, and commit both. A test fails when they differ.", "",
        f'**Rules version {register["rules_version"]}** · register updated {register["updated"]} · {len(rules)} rules: '
        f'{counts["compliance"]} compliance checks, {counts["cross_check"]} cross-checks, {counts["safety"]} safety rules '
        f'· first review due {first_due}', "",
        "The register is the single source of the legal basis the rules engine cites. Every row of the compliance "
        "checklist and every mismatch that `check_label` returns carries its `rule_id`, the citation, the date the "
        "rule applies from and how well that basis was checked, so a reviewer can trace any result to the text of "
        "the law. The engine reads this file at start-up; nothing about the legal basis is written in the prompt.", "",
        "## How to read it", "",
        "| Mark | Basis checked against | Effect in the engine |", "|---|---|---|",
        "| ✅ Primary | The official text | The check can pass or fail |",
        "| 🟡 Secondary | A reputable secondary source (agency guidance, legal database, trade body) | The check can "
        "pass or fail; confirm against the official text before a pilot |",
        "| ⚪ Unverified | Not checked yet | A checklist row never passes or fails there: it is always review. A "
        "cross-check still sends the label to a person, and its mismatch says the basis is unverified |",
        "| n/a | No legal text applies (a project safety rule or a consistency check) | — |", "",
        f'> [!WARNING]\n> **Not yet verified:** {"; ".join(unverified) if unverified else "none"}. Until someone '
        "reads the official text and updates the register, a checklist row on these rules returns review, and a "
        "contradiction they find is escalated with `content_verified: unverified`, never resolved by the tool.", "",
        "## Rules", "",
        "| Rule | Check | Type | Basis checked | Next review |", "|---|---|---|---|---|",
    ]
    for r in rules:
        out.append(f'| [{r["id"]}](#{r["id"].lower()}) | {cell(r["check"])} | {TYPE[r["type"]]} | {basis_summary(r)} '
                   f'| {next_review(r)} |')
    out += [
        "", "## How the register is governed", "",
        "| Control | Rule | Enforced by |", "|---|---|---|",
        f'| Verification | {cell(policy["content_verified"])} | The engine (`compliance_checklist`); test '
        "`test_unverified_basis_never_passes_or_fails` |",
        f'| Effective dates | {cell(policy["effective_source"])} | Shown on every checklist row (`effective_from`) |',
        f'| Review cadence | {cell(policy["review_cadence"])} | `test_no_review_is_overdue` |',
        f'| Change control | {cell(policy["change_control"])} | `test_register_version_matches_engine`, '
        "`test_every_rule_points_to_existing_tests`, `test_rule_register_page_is_up_to_date` |",
        "| Coverage | Every checklist row the engine emits names a rule. | "
        "`test_every_checklist_row_the_engine_emits_has_a_rule` |", "",
        "All of these run in continuous integration on every push "
        "([`test_rule_register.py`](../mcp-server/tests/test_rule_register.py)).", "",
        "### Release process for a rule change", "",
        "1. Open a **Rule change** issue ([form](../.github/ISSUE_TEMPLATE/rule-change.yml)): market, citation with "
        "a link to the official text, the date it applies from, the behaviour expected and an example label.",
        "2. Write the failing test first, with the example label.",
        "3. Change the engine and this rule's entry in the register: `applies`, a `history` line, `tests` and "
        "`last_reviewed`.",
        "4. Raise `rules_version` in the register and `RULES_VERSION` in `engine.py`: minor for a new or changed "
        "behaviour, patch for a citation or date fix. A test fails when the two differ.",
        "5. Run `uv run python rules/render.py`, `uv run pytest` and `uv run eval_rules.py` (and the benchmark when "
        "matching changes), then add a line to the [changelog](../agent/CHANGELOG.md).",
        "6. A second person, the regulatory owner, reviews the pull request. Every result names the rules version, "
        "so a past check can be traced to the rules it used.", "",
        "Disputed ingredient mappings (\"this term is not milk\") follow the same path with their own "
        "[form](../.github/ISSUE_TEMPLATE/disputed-mapping.yml); see "
        "[data governance](../mcp-server/data/README.md#governance).", "",
        "### What the register does not do yet", "",
        "- **Effective dates are recorded, not applied.** The engine checks every label against the rules in force "
        "now; a label printed before a rule applied needs a person (roadmap F-09).",
        "- **Thresholds and each market's allergen list still live in code** (`MARKET_ALLERGENS`); the register "
        "cites them. Moving them into data is F-09.",
        "- **The checks were made by the project author, not a regulatory professional.** The ⚪ and 🟡 rows are "
        "the first thing to confirm before a pilot.", "",
        "## Rule details", "",
    ]
    for r in rules:
        out += rule_section(r)
    return "\n".join(out).rstrip("\n") + "\n"


def main() -> None:
    PAGE.write_text(render(json.loads(REGISTER.read_text(encoding="utf-8"))), encoding="utf-8", newline="\n")
    print(f"wrote {PAGE}")


if __name__ == "__main__":
    main()
