"""Cross-check curated rows that have no cited source against the Open Food Facts taxonomies.

Usage: uv run data/crosscheck_curated.py [taxonomy folder] [--apply]

A row is "confirmed" when Open Food Facts has the same term with the same origin class and no allergen
disagreement in either direction. With --apply, confirmed rows get the Open Food Facts entry as their source;
conflicts and terms not found are never changed, only listed in tests/evidence/curated-crosscheck.md for review.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import engine  # noqa: E402
import import_off as off  # noqa: E402

UNSOURCED = ("v0.2-added", "v0.2.1-added")
REPORT = Path(__file__).parent.parent.parent / "tests" / "evidence" / "curated-crosscheck.md"
ORIGIN_CLASS = {"animal": "animal", "either": "either", "plant": "non_animal", "mineral_synthetic": "non_animal",
                "microbial": "non_animal", "non_animal": "non_animal"}


def split(s: str) -> set[str]:
    return {x for x in s.split(";") if x}


def compare(cur: dict, ref: dict | None) -> tuple[str, str]:
    if ref is None:
        return "not found", "no Open Food Facts entry with this name"
    problems = []
    if ORIGIN_CLASS.get(cur["origin"]) != ref["origin"]:
        problems.append(f"origin {cur['origin']} vs {ref['origin']}")
    cur_all, ref_all, ref_may = split(cur["allergens"]), split(ref["allergens"]), split(ref["may_allergens"])
    if missing := ref_all - cur_all:
        problems.append(f"Open Food Facts lists {', '.join(sorted(missing))}")
    if extra := cur_all - ref_all - ref_may:
        problems.append(f"curated lists {', '.join(sorted(extra))}, Open Food Facts rules it out")
    return ("conflict", "; ".join(problems)) if problems else ("confirmed", "")


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--apply"]
    folder = Path(args[0]) if args else None
    matcher = engine.Matcher(sources="curated")
    add_tax, add_txt = off.load(folder, "additives")
    ing_tax, ing_txt = off.load(folder, "ingredients")
    ref_rows = off.additive_rows(add_tax, off.parse_txt(add_txt, add_tax)) + \
        off.ingredient_rows(ing_tax, off.parse_txt(ing_txt, ing_tax), matcher)
    ref = {r["term"]: r for r in off.merge(ref_rows, set()) if r["lang"] in off.BASE_LANGS + ("xx",)}

    with open(engine.CSV_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    results = []
    for r in rows:
        if r["source"] in UNSOURCED:
            hit = ref.get(engine.normalize(r["term"]))
            status, detail = compare(r, hit)
            results.append((r, status, detail, hit["source"] if hit else ""))
            if status == "confirmed" and "--apply" in sys.argv:
                r["source"] = f"{r['source']}; confirmed by {hit['source']}"
    if "--apply" in sys.argv:
        with open(engine.CSV_PATH, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, list(rows[0].keys()), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    counts = {s: sum(1 for _, st, _, _ in results if st == s) for s in ("confirmed", "conflict", "not found")}
    lines = ["# Curated rows without a source, cross-checked against Open Food Facts", "",
             f"{len(results)} rows checked: {counts['confirmed']} confirmed, {counts['conflict']} in conflict, "
             f"{counts['not found']} not found. Confirmed rows now cite the Open Food Facts entry. "
             "Conflicts and missing terms need a person to decide, with an official or scientific source.", "",
             "| Term | Origin | Allergens | Result | Detail | Open Food Facts entry |", "|---|---|---|---|---|---|"]
    order = {"conflict": 0, "not found": 1, "confirmed": 2}
    for r, status, detail, src in sorted(results, key=lambda x: (order[x[1]], x[0]["term"])):
        lines.append(f"| {r['term']} | {r['origin']} | {r['allergens'] or '-'} | {status} | {detail or '-'} | "
                     f"{src or '-'} |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(counts)


if __name__ == "__main__":
    main()
