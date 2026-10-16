"""Freeze a benchmark sample of real products from the Open Food Facts CSV export.

Usage (needs Python 3.12 for the duckdb wheel):
    curl -L -o products.csv.gz https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz
    uv run --no-project --python 3.12 --with duckdb python tests/benchmark/build_sample.py products.csv.gz

For each market (country where the product is sold), takes the most scanned products that have an ingredient
list, with the allergens and traces Open Food Facts records for them and the diet and free-from labels.
A product sold in several of these markets is counted once, in the first market listed. The sample is written to
tests/benchmark/off-products.jsonl, so every benchmark run uses the same data.
Data: Open Food Facts, © Open Food Facts contributors, ODbL 1.0.
"""

import json
import sys
from pathlib import Path

import duckdb

OUT = Path(__file__).parent / "off-products.jsonl"
MARKETS = {"BR": ("en:brazil", "pt", 2000), "US": ("en:united-states", "en", 2000),
           "FR": ("en:france", "fr", 1000), "DE": ("en:germany", "de", 1000)}
KEEP_LABELS = ("vegan", "vegetarian", "gluten", "lactose", "milk")


def tags(s: str | None) -> list[str]:
    return sorted({t for t in (s or "").split(",") if t})


def main() -> None:
    path = sys.argv[1]
    con = duckdb.connect()
    con.execute(f"""
        CREATE TABLE p AS
        SELECT code, product_name, ingredients_text, allergens, traces_tags, labels_tags, countries_tags,
               TRY_CAST(unique_scans_n AS INTEGER) AS scans
        FROM read_csv('{path}', delim='\t', quote='', escape='', header=true, all_varchar=true,
                      ignore_errors=true, strict_mode=false, max_line_size=10000000)
        WHERE length(ingredients_text) > 10
          AND (countries_tags LIKE '%en:brazil%' OR countries_tags LIKE '%en:united-states%'
               OR countries_tags LIKE '%en:france%' OR countries_tags LIKE '%en:germany%')""")
    used = set()
    with OUT.open("w", encoding="utf-8") as f:
        for market, (country, lang, n) in MARKETS.items():
            rows = con.execute("""SELECT code, product_name, ingredients_text, allergens, traces_tags, labels_tags, scans
                                  FROM p WHERE list_contains(string_split(countries_tags, ','), ?)
                                  ORDER BY scans DESC NULLS LAST LIMIT ?""", [country, n * 2]).fetchall()
            kept = 0
            for code, name, text, allergens, traces, labels, scans in rows:
                if code in used or kept >= n:
                    continue
                used.add(code)
                kept += 1
                f.write(json.dumps({
                    "market": market, "lang": lang, "code": code, "scans": scans, "name": name or "",
                    "ingredients": " ".join(text.replace("\\n", " ").split()),
                    "allergens": tags(allergens), "traces": tags(traces),
                    "labels": [l for l in tags(labels) if any(k in l for k in KEEP_LABELS)],
                }, ensure_ascii=False) + "\n")
            print(f"{market}: {kept} products", flush=True)


if __name__ == "__main__":
    main()
