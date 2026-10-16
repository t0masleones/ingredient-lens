"""Run the rules engine over the frozen sample of real products and write the evidence report.

Usage: uv run --directory mcp-server python ../tests/benchmark/run_benchmark.py

Reference data: the allergens Open Food Facts records for each product (declared by the manufacturer or derived
from the ingredient list by Open Food Facts) and the labels on the pack (vegan, gluten-free, lactose-free).
Neither was used to write the rules, but the allergen tags are partly derived with the same taxonomy this project
imports, so the allergen figures are an upper bound on agreement, not an independent truth.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "mcp-server"))
import engine  # noqa: E402

SAMPLE = Path(__file__).parent / "off-products.jsonl"
REPORT = ROOT / "tests" / "evidence" / f"benchmark-rules-v{engine.RULES_VERSION.rsplit('.', 1)[0]}.md"
SUMMARY = Path(__file__).parent / "results.json"
OFF_TO_GROUP = {"en:milk": "milk", "en:eggs": "egg", "en:fish": "fish", "en:crustaceans": "crustacean",
                "en:molluscs": "mollusc", "en:gluten": "gluten", "en:soybeans": "soy", "en:peanuts": "peanut",
                "en:nuts": "tree_nuts", "en:sesame-seeds": "sesame", "en:celery": "celery", "en:mustard": "mustard",
                "en:lupin": "lupin", "en:sulphur-dioxide-and-sulphites": "sulphites"}
MARKET_RULES = {"BR": "BR", "US": "US", "FR": "EU", "DE": "EU"}
MAY_MILK = {"pt": "Pode conter leite.", "en": "May contain milk.", "fr": "Peut contenir du lait.",
            "de": "Kann Spuren von Milch enthalten."}
CLAIMS = {"vegan": ("vegan", {"en:vegan"}), "gluten": ("gluten", {"en:no-gluten", "en:gluten-free"}),
          "lactose": ("lactose", {"en:no-lactose", "en:lactose-free"})}
RANK = engine.RANK


def label_text(p: dict) -> str:
    text = p["ingredients"]
    return text if engine.HEADER.search(text) else f"INGREDIENTS: {text}"


def main() -> None:
    products = [json.loads(line) for line in SAMPLE.open(encoding="utf-8")]
    m = engine.Matcher()
    timings = []

    def check(text, avoid, strict=False, market="BR"):
        t = time.perf_counter()
        r = engine.check_label(text, avoid, strict, market, matcher=m)
        timings.append((time.perf_counter() - t) * 1000)
        return r

    allergen = defaultdict(Counter)            # (market, group) -> verdict counts (normal mode)
    allergen_strict = defaultdict(Counter)
    misses = []
    claims = defaultdict(Counter)
    claim_conflicts = []
    coverage = defaultdict(lambda: [0, 0])
    unknown = defaultdict(Counter)
    meta = Counter()
    meta_fail = defaultdict(list)

    for p in products:
        mk, rules_market, text = p["market"], MARKET_RULES[p["market"]], label_text(p)
        base = check(text, [], market=rules_market)
        if base["verdict"] == "insufficient":
            coverage[mk][1] += 0
            continue
        for i in base["ingredients"]:
            coverage[mk][1] += 1
            if i["matched_terms"]:
                coverage[mk][0] += 1
            else:
                unknown[mk][engine.normalize(i["text"])[:40]] += 1

        groups = sorted({OFF_TO_GROUP[a] for a in p["allergens"] if a in OFF_TO_GROUP})
        for g in groups:
            r = check(text, [g], market=rules_market)
            allergen[(mk, g)][r["verdict"]] += 1
            allergen_strict[(mk, g)][check(text, [g], True, rules_market)["verdict"]] += 1
            if r["verdict"] == "green":
                misses.append((mk, g, p["code"], p["name"], p["ingredients"][:160]))

        for name, (avoid, tags) in CLAIMS.items():
            if tags & set(p["labels"]):
                r = check(text, [avoid], market=rules_market)
                claims[(mk, name)][r["verdict"]] += 1
                if r["verdict"] == "red":
                    why = "; ".join(f"{f['ingredient']}: {f['why']}" for f in r["findings"] if f["level"] == "red")
                    claim_conflicts.append((mk, name, p["code"], p["name"], why[:160]))

        # Metamorphic relations: properties that must hold for any label.
        for avoid in ["lactose", "gluten", "vegan"] + groups:
            normal = check(text, [avoid], market=rules_market)
            relations = {
                "same input, same verdict": check(text, [avoid], market=rules_market)["verdict"] == normal["verdict"],
                "upper case does not change the verdict":
                    check(text.upper(), [avoid], market=rules_market)["verdict"] == normal["verdict"],
                "STRICT is never milder":
                    RANK[check(text, [avoid], True, rules_market)["verdict"]] >= RANK[normal["verdict"]],
            }
            items = [i["text"] for i in normal["ingredients"]]
            if len(items) > 1:
                fwd = check("INGREDIENTS: " + ", ".join(items) + ".", [avoid], market=rules_market)["verdict"]
                rev = check("INGREDIENTS: " + ", ".join(reversed(items)) + ".", [avoid], market=rules_market)["verdict"]
                relations["ingredient order does not change the verdict"] = fwd == rev
            if avoid in ("lactose",):
                more = check(f"{text.rstrip('. ')}. {MAY_MILK[p['lang']]}", ["milk"], market=rules_market)
                was = check(text, ["milk"], market=rules_market)
                relations["adding 'may contain milk' never improves a milk verdict"] = (
                    RANK[more["verdict"]] >= RANK[was["verdict"]] and more["verdict"] != "green")
            for rel, ok in relations.items():
                meta[(rel, ok)] += 1
                if not ok and len(meta_fail[rel]) < 5:
                    meta_fail[rel].append((p["code"], avoid, p["ingredients"][:120]))

    # ------------------------------------------------------------------ report
    def pct(a, b):
        return f"{a / b:.1%}" if b else "-"

    n_checks = len(timings)
    lines = [f"# Rules engine benchmark on real products (rules {engine.RULES_VERSION})", "",
             f"{len(products)} products from Open Food Facts (most scanned per market, ingredient list in the label "
             f"language), {n_checks:,} engine runs, data {m.data_version} terms. Sample: "
             "`tests/benchmark/off-products.jsonl` (ODbL). Reproduce: `uv run --directory mcp-server python "
             "../tests/benchmark/run_benchmark.py`.", "",
             "**How to read it.** Reference allergens are what Open Food Facts records for each product. They come "
             "from manufacturers and from Open Food Facts' own parsing, which uses the same taxonomy this project "
             "imports, so agreement is an upper bound. Labels (vegan, gluten-free, lactose-free) are claims printed on "
             "the pack. The ingredient text alone is checked: a separate allergen box that was not transcribed into "
             "the ingredient field is invisible to the engine.", "",
             "## 1. Safety: declared allergens the engine missed (false greens)", "",
             "| Market | Allergen | Products | 🔴 | 🟡 | 🟢 missed | Miss rate | Miss rate in STRICT |",
             "|---|---|---|---|---|---|---|---|"]
    tot = Counter()
    tot_strict = Counter()
    for (mk, g), c in sorted(allergen.items()):
        n = sum(c.values())
        s = allergen_strict[(mk, g)]
        tot.update(c)
        tot_strict.update(s)
        lines.append(f"| {mk} | {g} | {n} | {c['red']} | {c['yellow']} | {c['green']} | {pct(c['green'], n)} | "
                     f"{pct(s['green'], n)} |")
    n_all = sum(tot.values())
    lines += [f"| **All** | | **{n_all}** | {tot['red']} | {tot['yellow']} | **{tot['green']}** | "
              f"**{pct(tot['green'], n_all)}** | **{pct(tot_strict['green'], n_all)}** |", "",
              "### Missed allergens (first 40)", "", "| Market | Allergen | Product | Ingredient text (start) |",
              "|---|---|---|---|"]
    for mk, g, code, name, txt in misses[:40]:
        lines.append(f"| {mk} | {g} | {name[:40]} ({code}) | {txt.replace('|', '/')} |")

    lines += ["", "## 2. Claims on the pack vs the engine", "",
              "A 🔴 here means the engine found something that contradicts the claim: an engine false alarm, a "
              "data error or a real labeling issue. Each one needs a person to look.", "",
              "| Market | Claim | Products | 🟢 | 🟡 | 🔴 conflict |", "|---|---|---|---|---|---|"]
    for (mk, name), c in sorted(claims.items()):
        lines.append(f"| {mk} | {name} | {sum(c.values())} | {c['green']} | {c['yellow']} | {c['red']} |")
    lines += ["", "### Conflicts (first 30)", "", "| Market | Claim | Product | Why the engine says 🔴 |",
              "|---|---|---|---|"]
    for mk, name, code, pname, why in claim_conflicts[:30]:
        lines.append(f"| {mk} | {name} | {pname[:40]} ({code}) | {why.replace('|', '/')} |")

    lines += ["", "## 3. Coverage: ingredients found in the database", "",
              "| Market | Ingredients | Found | Coverage | Most frequent unknown items |", "|---|---|---|---|---|"]
    for mk in ("BR", "US", "FR", "DE"):
        f, t = coverage[mk]
        top = ", ".join(f"{k} ({v})" for k, v in unknown[mk].most_common(12))
        lines.append(f"| {mk} | {t} | {f} | {pct(f, t)} | {top.replace('|', '/')} |")

    lines += ["", "## 4. Metamorphic tests (properties that must hold for any label)", "",
              "| Property | Checks | Failures |", "|---|---|---|"]
    rels = sorted({rel for rel, _ in meta})
    for rel in rels:
        ok, bad = meta[(rel, True)], meta[(rel, False)]
        lines.append(f"| {rel} | {ok + bad:,} | {bad} |")
    for rel, fails in meta_fail.items():
        lines += ["", f"Examples of failures, {rel}:"] + [f"- {c} ({a}): {t}" for c, a, t in fails]

    lines += ["", "## 5. Performance", "",
              f"{n_checks:,} engine runs: median {statistics.median(timings):.1f} ms, "
              f"95th percentile {statistics.quantiles(timings, n=20)[18]:.1f} ms per label.", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "rules_version": engine.RULES_VERSION, "products": len(products), "engine_runs": n_checks,
        "allergen_checks": n_all, "false_greens": tot["green"], "false_green_rate": tot["green"] / n_all if n_all else 0,
        "false_greens_strict": tot_strict["green"],
        "claims": {f"{mk}/{n}": dict(c) for (mk, n), c in claims.items()},
        "coverage": {mk: round(f / t, 4) if t else 0 for mk, (f, t) in coverage.items()},
        "metamorphic_checks": sum(meta.values()), "metamorphic_failures": sum(v for (r, ok), v in meta.items() if not ok),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
