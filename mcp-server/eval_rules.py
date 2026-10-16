"""Run the text rows of tests/golden-set.csv through the rules engine and compare verdicts.

Usage: uv run eval_rules.py   (writes tests/evidence/results-rules-v0.2.md)
"""

import csv
import re
import sys
from pathlib import Path

import engine

ROOT = Path(__file__).parent.parent
GOLDEN = ROOT / "tests" / "golden-set.csv"
OUT = ROOT / "tests" / "evidence" / f"results-rules-v{engine.RULES_VERSION.rsplit('.', 1)[0]}.md"
ICON = {"🔴": "red", "🟡": "yellow", "🟢": "green"}
PROFILE_WORDS = {"lactose": "lactose", "gluten": "gluten", "celiac": "gluten", "milk allergy": "milk",
                 "peanut": "peanut", "tree nut": "tree_nuts", "vegan": "vegan", "vegetarian": "vegetarian"}


def parse_profile(text: str) -> tuple[list[str], bool]:
    text = text.lower()
    avoid = [v for k, v in PROFILE_WORDS.items() if re.search(rf"\b{k}", text)]
    return list(dict.fromkeys(avoid)), "strict" in text


def expected(row: dict) -> str | None:
    if row["expected_verdict"].startswith("Escalate"):
        return "escalate"
    return next((v for k, v in ICON.items() if k in row["expected_verdict"]), None)


def main() -> None:
    matcher = engine.Matcher(engine.connect())
    rows = [r for r in csv.DictReader(open(GOLDEN, encoding="utf-8")) if expected(r)]
    lines = [f"# Rules engine vs golden set (rules {engine.RULES_VERSION})", "",
             "Deterministic layer only: no LLM, no photos. Photo and edge cases are tested in the Claude chat.", "",
             "| ID | Profile | Expected | Rules engine | Escalate | Coverage | Pass |", "|---|---|---|---|---|---|---|"]
    passed = 0
    for r in rows:
        avoid, strict = parse_profile(r["profile"])
        res = engine.check_label(r["input"], avoid, strict, matcher=matcher)
        want = expected(r)
        got = "escalate" if want == "escalate" and res["escalate_to_human_review"] else res["verdict"]
        ok = got == want
        passed += ok
        lines.append(f"| {r['id']} | {r['profile']} | {want} | {res['verdict']} | "
                     f"{'yes' if res.get('escalate_to_human_review') else 'no'} | {res.get('coverage', '')} | "
                     f"{'✅' if ok else '❌'} |")
    lines += ["", f"**Pass rate: {passed}/{len(rows)} ({passed / len(rows):.0%})**", ""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252 when output is redirected
    print("\n".join(lines))


if __name__ == "__main__":
    main()
