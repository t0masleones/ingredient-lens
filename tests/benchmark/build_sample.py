"""Freeze a benchmark sample of real products from the Open Food Facts CSV export.

Usage (needs Python 3.12 for the duckdb wheel):
    curl -L -o products.csv.gz https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz
    uv run --no-project --python 3.12 --with duckdb python tests/benchmark/build_sample.py products.csv.gz

For each market (country where the product is sold), takes the most scanned products that pass the quality gate
(F-28), with the allergens and traces Open Food Facts records for them and the diet and free-from labels:
- the ingredient text is in the market's language, detected from the text itself (`detect_language`), because a
  product sold in a country often carries a foreign label;
- at least MIN_SCANS unique scans for the market (none in Brazil) and MIN_COMPLETENESS, with the ingredients marked completed by contributors and
  no data quality error recorded.
A product sold in several of these markets is counted once, in the first market listed. The sample is written to
tests/benchmark/off-products.jsonl, and the source dump, filters and drop counts to off-products.meta.json, so every
benchmark run uses the same data and the sample can be traced to its dump.
Data: Open Food Facts, © Open Food Facts contributors, ODbL 1.0.
"""

import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent / "off-products.jsonl"
META = Path(__file__).parent / "off-products.meta.json"
MARKETS = {"BR": ("en:brazil", "pt", 2000), "US": ("en:united-states", "en", 2000),
           "FR": ("en:france", "fr", 1000), "DE": ("en:germany", "de", 1000)}
KEEP_LABELS = ("vegan", "vegetarian", "gluten", "lactose", "milk")
# Brazil has little scan traffic on Open Food Facts: with 5 scans only 87 Portuguese labels remain, so there
# scans only order the products and the other gates carry the quality.
MIN_SCANS = {"BR": 0, "US": 5, "FR": 5, "DE": 5}
MIN_COMPLETENESS = 0.5

# Words common in ingredient lists, per language. Languages outside the markets are here so a Spanish or Italian
# label is not taken for Portuguese or French. A word shared by several languages counts less.
STOPWORDS = {
    "pt": "de e com açúcar sal farinha leite óleo água contém pode conter trigo ovo ovos corante fermento amido "
          "glúten ingredientes vegetal natural regulador acidez conservador espessante emulsificante milho gordura "
          "xarope extrato aromatizante não da do",
    "en": "and of with sugar salt flour milk oil water contains may wheat egg eggs flavor flavour natural color "
          "colour starch corn syrup vegetable acid less than or the powder modified ingredients",
    "fr": "et de du des la le sucre sel farine lait huile eau contient peut blé oeuf œuf arôme arômes naturel "
          "colorant amidon sirop végétale acide traces poudre émulsifiant ingrédients",
    "de": "und mit zucker salz mehl milch öl wasser enthält kann spuren weizen ei natürliches farbstoff stärke "
          "sirup pflanzliches säure pulver emulgator von aus zutaten",
    "es": "y con azúcar sal harina leche aceite agua contiene puede trigo huevo natural colorante almidón jarabe "
          "vegetal ácido polvo emulgente ingredientes de",
    "it": "e con zucchero sale farina latte olio acqua contiene può frumento uovo aromi naturale colorante amido "
          "sciroppo vegetale acido polvere emulsionante ingredienti di",
    "nl": "en met suiker zout bloem melk olie water bevat kan tarwe ei natuurlijk kleurstof zetmeel siroop "
          "plantaardige zuur poeder emulgator van ingrediënten",
}
STOPWORDS = {lang: set(words.split()) for lang, words in STOPWORDS.items()}
WEIGHT = Counter(w for words in STOPWORDS.values() for w in words)
MIN_SCORE, MIN_MARGIN = 1.5, 1.5


def detect_language(text: str) -> str | None:
    """The language of an ingredient text, or None when no language leads clearly (too short, or bilingual)."""
    tokens = re.findall(r"[^\W\d_]+", text.lower())
    scores = {lang: sum(1 / WEIGHT[t] for t in tokens if t in words) for lang, words in STOPWORDS.items()}
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    (best, top), (_, second) = ranked[0], ranked[1]
    return best if top >= MIN_SCORE and top >= MIN_MARGIN * second else None


def tags(s: str | None) -> list[str]:
    return sorted({t for t in (s or "").split(",") if t})


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    import duckdb

    path = sys.argv[1]
    con = duckdb.connect()
    con.execute(f"""
        CREATE TABLE p AS
        SELECT code, product_name, ingredients_text, allergens_tags, traces_tags, labels_tags, countries_tags,
               states_tags, data_quality_errors_tags, TRY_CAST(completeness AS DOUBLE) AS completeness,
               TRY_CAST(unique_scans_n AS INTEGER) AS scans, last_modified_t AS modified
        FROM read_csv('{path}', delim='\t', quote='', escape='', header=true, all_varchar=true,
                      ignore_errors=true, strict_mode=false, max_line_size=10000000)
        WHERE length(ingredients_text) > 10
          AND (countries_tags LIKE '%en:brazil%' OR countries_tags LIKE '%en:united-states%'
               OR countries_tags LIKE '%en:france%' OR countries_tags LIKE '%en:germany%')""")
    used = set()
    meta = {"source": "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz",
            "source_sha256": sha256(path),
            "latest_product_modified": con.execute("SELECT max(modified) FROM p").fetchone()[0],
            "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "filters": {"min_scans": MIN_SCANS, "min_completeness": MIN_COMPLETENESS,
                        "states": "en:ingredients-completed", "data_quality_errors": "none",
                        "language": f"detected from the text, score >= {MIN_SCORE}, margin >= {MIN_MARGIN}"},
            "markets": {}}
    with OUT.open("w", encoding="utf-8") as f:
        for market, (country, lang, n) in MARKETS.items():
            rows = con.execute("""SELECT code, product_name, ingredients_text, allergens_tags, traces_tags, labels_tags,
                                         scans
                                  FROM p WHERE list_contains(string_split(countries_tags, ','), ?)
                                    AND coalesce(scans, 0) >= ? AND completeness >= ?
                                    AND states_tags LIKE '%en:ingredients-completed%'
                                    AND coalesce(data_quality_errors_tags, '') = ''
                                  ORDER BY scans DESC NULLS LAST, code""", [country, MIN_SCANS[market], MIN_COMPLETENESS]).fetchall()
            dropped = Counter()
            kept = 0
            for code, name, text, allergens, traces, labels, scans in rows:
                if kept >= n:
                    break
                if code in used:
                    dropped["other_market"] += 1
                    continue
                text = " ".join(text.replace("\\n", " ").split())
                detected = detect_language(text)
                if detected != lang:
                    dropped[f"language_{detected or 'unclear'}"] += 1
                    continue
                used.add(code)
                kept += 1
                f.write(json.dumps({
                    "market": market, "lang": lang, "code": code, "scans": scans, "name": name or "",
                    "ingredients": text, "allergens": tags(allergens), "traces": tags(traces),
                    "labels": [l for l in tags(labels) if any(k in l for k in KEEP_LABELS)],
                }, ensure_ascii=False) + "\n")
            meta["markets"][market] = {"kept": kept, "target": n, "dropped": dict(sorted(dropped.items()))}
            print(f"{market}: {kept} products, dropped {dict(dropped)}", flush=True)
    META.write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
