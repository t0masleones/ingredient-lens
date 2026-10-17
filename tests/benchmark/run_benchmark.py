"""Run the rules engine over the frozen sample of real products and write the evidence report.

Usage: uv run --directory mcp-server python ../tests/benchmark/run_benchmark.py

Two references, reported separately:
- A. The allergens Open Food Facts records for each product (declared by manufacturers or derived by Open Food Facts
  with the same taxonomy this project imports): broad, but partly coupled to the engine, so an upper bound.
- B. The manufacturer's own allergen statement when it appears in the ingredient text ("ALÉRGICOS: CONTÉM ...",
  "CONTAINS: ..."): narrower, independent of Open Food Facts tags.
Misses against reference A are sorted into the four failure buckets of the external review (ingestion, parsing,
taxonomy, reference definition) with a keyword list that does not use the engine's vocabulary.
"""

from __future__ import annotations

import csv
import re
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
GROUPS = sorted(set(OFF_TO_GROUP.values()))
MARKETS = ("BR", "US", "FR", "DE")
MARKET_RULES = {"BR": "BR", "US": "US", "FR": "EU", "DE": "EU"}
MAY_MILK = {"pt": "Pode conter leite.", "en": "May contain milk.", "fr": "Peut contenir du lait.",
            "de": "Kann Spuren von Milch enthalten."}
CLAIMS = {"vegan": ("vegan", {"en:vegan"}), "gluten": ("gluten", {"en:no-gluten", "en:gluten-free"}),
          "lactose": ("lactose", {"en:no-lactose", "en:lactose-free"})}
RANK = engine.RANK
# Independent of the engine's database: words a person would look for, in the label languages of the sample.
KEYWORDS = {
    "milk": "leite lacteo milk lait laitier milch latte melk leche whey soro lactose lactosa butter manteiga beurre "
            "cream creme nata sahne panna cheese queijo fromage kase formaggio yogurt iogurte yaourt joghurt casein "
            "caseina caseinate lactoserum buttermilk",
    "gluten": "trigo wheat ble weizen frumento grano tarwe cevada barley orge gerste orzo centeio rye seigle roggen "
              "segale aveia oat oats avoine hafer avena espelta spelt epeautre dinkel farro malte malt gluten glutine "
              "semolina semoule couscous bulgur kamut triticale",
    "egg": "ovo ovos egg eggs oeuf oeufs ei eier uovo uova huevo albumina albumen",
    "soy": "soja soy soya edamame tofu",
    "peanut": "amendoim peanut peanuts cacahuete arachide arachides erdnuss erdnusse arachidi mani",
    "tree_nuts": "castanha castanhas nut nuts noz nozes amendoa amendoas almond almonds avela hazelnut hazelnuts "
                 "noisette noisettes haselnuss haselnusse cashew caju pecan pistache pistachio pistazie macadamia "
                 "walnut walnuts noix mandel mandeln nocciola nocciole mandorla mandorle",
    "sesame": "gergelim sesame sesamo sesam tahini tahine",
    "fish": "peixe fish poisson fisch pesce atum tuna thon salmao salmon saumon lachs anchova anchovy anchois "
            "sardinha sardine bacalhau cod",
    "crustacean": "camarao shrimp prawn crevette garnele gamberi caranguejo crab crabe lobster lagosta homard",
    "mollusc": "molusco moluscos mollusc squid lula octopus polvo mussel mexilhao oyster ostra calamar",
    "celery": "aipo salsao celery celeri sellerie sedano apio",
    "mustard": "mostarda mustard moutarde senf senape mostaza",
    "sulphites": "sulfito sulfitos sulphite sulphites sulfite sulfites e220 e221 e222 e223 e224 e225 e226 e227 e228 "
                 "metabissulfito disulfite bisulfite anidrido",
    "lupin": "tremoco lupin lupine lupino altramuz lupinen",
}
KEYWORDS = {g: set(v.split()) for g, v in KEYWORDS.items()}
BUCKETS = [
    ("definition", "Reference definition mismatch", "The allergen is not in the ingredient text: the reference took it "
     "from traces, a separate allergen box or a data error"),
    ("ingestion", "Ingestion failure", "The ingredient text is unreadable or garbled (OCR)"),
    ("taxonomy", "Taxonomy or regulation mismatch", "The reference and the regulation or the label disagree "
     "(for example coconut as a tree nut; a gluten-free label)"),
    ("parsing", "Engine parsing or vocabulary failure", "The allergen is readable in the text and the engine missed it: "
     "a real engine error to fix"),
]


def label_text(p: dict) -> str:
    text = p["ingredients"]
    return text if engine.HEADER.search(text) else f"INGREDIENTS: {text}"


def mentions(group: str, text: str) -> bool:
    """Whether a person scanning the text would see the allergen: exact short words, prefixes for longer ones
    (so "haselnussen" matches "haselnuss")."""
    tokens = {t.strip(".,;:()[]*%_'\"") for t in text.replace("/", " ").split()}
    return any(tok == k or (len(k) >= 4 and tok.startswith(k)) for tok in tokens for k in KEYWORDS[group])


# Phrases that contain a dairy word but are not dairy (cocoa butter, peanut butter, coconut milk...).
NOT_DAIRY = re.compile(r"\b(cocoa|cacao|kakao|peanut|cacahuete|shea|karite)\s+(butter|beurre)\b|\bkakaobutter\b|"
                       r"\b(beurre|manteiga|mantequilla|burro)\s+(de|di)\s+(cacao|cacau|cacahuete|amendoim|karite|cacahuate)\b|"
                       r"\b(coconut|coco)\s+(milk|cream)\b|\b(lait|leite|leche|latte|creme|crema)\s+(de|di)\s+coco\b")


def bucket_for(group: str, p: dict, base: dict) -> str:
    """Which of the four buckets a missed allergen belongs to (reference A). Order matters: an unreadable text is
    an ingestion failure whatever it mentions; a known reference disagreement is checked before absence."""
    text = engine.normalize(p["ingredients"])
    items = base.get("ingredients", [])
    unknown = sum(1 for i in items if not i["matched_terms"])
    if items and unknown / len(items) >= 0.6:
        return "ingestion"
    if group == "tree_nuts" and "coco" in text:
        return "taxonomy"
    if group == "gluten" and engine.GLUTEN_FREE.search(text):
        return "taxonomy"
    if group == "milk":
        text = NOT_DAIRY.sub(" ", text)
    if not mentions(group, text):
        return "definition"
    return "parsing"


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
    not_declared = defaultdict(Counter)        # (market, group) -> {"n": products without the tag, "red": flagged}
    extraction = defaultdict(Counter)          # market -> counters
    ref_b = defaultdict(Counter)               # market -> statement reference counters
    alarm_examples, xc2_examples = [], []
    claims = defaultdict(Counter)
    claim_conflicts = []
    coverage = defaultdict(lambda: [0, 0])
    unknown = defaultdict(Counter)
    meta = Counter()
    meta_fail = defaultdict(list)

    for p in products:
        mk, rules_market, text = p["market"], MARKET_RULES[p["market"]], label_text(p)
        base = check(text, [], market=rules_market)
        extraction[mk]["products"] += 1
        if base["verdict"] in ("insufficient", "needs_manual_review"):
            continue
        st = base["statements"]
        extraction[mk]["ingredient_list"] += 1
        extraction[mk]["allergen_statement"] += bool(st["allergen_statement_found"])
        extraction[mk]["gluten_statement"] += st["gluten"] != "not found"
        extraction[mk]["any_statement"] += bool(st["allergen_statement_found"] or st["gluten"] != "not found"
                                                or st["lactose"] != "not found")
        for i in base["ingredients"]:
            coverage[mk][1] += 1
            if i["matched_terms"]:
                coverage[mk][0] += 1
            else:
                unknown[mk][engine.normalize(i["text"])[:40]] += 1

        # Reference A: allergens recorded by Open Food Facts.
        groups = sorted({OFF_TO_GROUP[a] for a in p["allergens"] if a in OFF_TO_GROUP})
        for g in groups:
            r = check(text, [g], market=rules_market)
            allergen[(mk, g)][r["verdict"]] += 1
            allergen_strict[(mk, g)][check(text, [g], True, rules_market)["verdict"]] += 1
            if r["verdict"] == "green":
                misses.append({"market": mk, "group": g, "code": p["code"], "name": p["name"],
                               "text": p["ingredients"][:160], "bucket": bucket_for(g, p, base)})
        # False-alarm proxy: flagged red for an allergen the reference does not record. Split by whether the
        # independent keyword list sees the allergen in the text (then the reference is incomplete) or not (then
        # it may be an engine false alarm, to read by hand).
        everything = check(text, GROUPS, market=rules_market)
        levels = defaultdict(lambda: "green")
        for f in everything["findings"]:
            levels[f["restriction"]] = engine.worst(levels[f["restriction"]], f["level"])
        norm_text = engine.normalize(p["ingredients"])
        for g in GROUPS:
            if g not in groups:
                not_declared[(mk, g)]["n"] += 1
                if levels[g] == "red":
                    not_declared[(mk, g)]["red"] += 1
                    named = mentions(g, NOT_DAIRY.sub(" ", norm_text) if g == "milk" else norm_text)
                    not_declared[(mk, g)]["named" if named else "not_named"] += 1
                    if not named:
                        why = "; ".join(f"{f['ingredient']}: {f['why']}" for f in everything["findings"]
                                        if f["restriction"] == g and f["level"] == "red")
                        alarm_examples.append((mk, g, p["code"], p["name"], why[:140]))

        # Reference B: the manufacturer's own allergen statement in the text. The ingredients are checked alone,
        # without the statement, so the engine cannot "find" an allergen by reading the declaration.
        declared = set(st["contains"])
        if declared:
            items = [i["text"] for i in base["ingredients"]]
            required = sorted(engine.MARKET_ALLERGENS[rules_market])
            alone = check("INGREDIENTS: " + ", ".join(items) + ".", sorted(set(required) | declared),
                          market=rules_market)
            lv = defaultdict(lambda: "green")
            for f in alone["findings"]:
                lv[f["restriction"]] = engine.worst(lv[f["restriction"]], f["level"])
            b = ref_b[mk]
            b["products"] += 1
            b["declared"] += len(declared)
            b["declared_flagged"] += sum(lv[g] != "green" for g in declared)
            b["declared_red"] += sum(lv[g] == "red" for g in declared)
            b["required_red"] += sum(lv[g] == "red" for g in required)
            b["required_red_declared"] += sum(lv[g] == "red" and g in declared for g in required)
            xc2 = [x for x in base["mismatches"] if x["rule"] == "XC2"]
            b["xc2"] += bool(xc2)
            if xc2:
                xc2_examples.append((mk, p["code"], p["name"], xc2[0]["issue"], p["ingredients"][:150]))

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

    golden = list(csv.DictReader(open(ROOT / "tests" / "golden-set.csv", encoding="utf-8")))
    recipes = sum(1 for r in golden if r["id"].startswith("V"))
    photos = sum(1 for r in golden if r["type"] == "photo")
    tot_products = sum(extraction[mk]["products"] for mk in MARKETS)
    tot_lists = sum(extraction[mk]["ingredient_list"] for mk in MARKETS)
    n_checks = len(timings)
    lines = [f"# Rules engine benchmark on real products (rules {engine.RULES_VERSION})", "",
             f"{len(products):,} products from Open Food Facts (most scanned in BR, US, FR and DE), "
             f"{n_checks:,} engine runs, data {m.data_version} terms (sha256 {engine.DATA_HASH}). Sample: "
             "`tests/benchmark/off-products.jsonl` (ODbL). Reproduce: `uv run --directory mcp-server python "
             "../tests/benchmark/run_benchmark.py`.", "",
             "> [!NOTE]",
             "> **Two references.** A = the allergens Open Food Facts records (broad, but partly derived with the "
             "taxonomy this project imports, so an upper bound). B = the manufacturer's own allergen statement when it "
             "is in the ingredient text (narrower, independent of those tags). Only the ingredient text is checked: an "
             "allergen box printed elsewhere on the pack is invisible here.", "",
             "## 1. Ingestion: how often the text could be read and split", "",
             "| Input type | Cases | Ingredient list extracted | Allergen statement found | Gluten statement found (BR) |",
             "|---|---|---|---|---|"]
    br = extraction["BR"]
    lines += [f"| Text (product ingredient field) | {tot_products:,} | {pct(tot_lists, tot_products)} | "
              f"{pct(sum(extraction[mk]['allergen_statement'] for mk in MARKETS), tot_lists)} | "
              f"{pct(br['gluten_statement'], br['ingredient_list'])} |",
              f"| Recipe (typed list) | {recipes} golden cases | measured in the golden set only | n/a | n/a |",
              f"| Photo | 0 at scale ({photos} golden cases not run) | **not measured** | **not measured** | "
              "**not measured** |", "",
              "Statements are often missing because the Open Food Facts ingredient field usually stores only the list, "
              "not the allergen or gluten box; on a real pack the agent must transcribe every panel. Photo reading, "
              "the most common real input, is the largest unmeasured risk (roadmap F-02); the ingestion gate "
              "(rule INGEST-GATE) blocks or degrades checks when a reading is unsure.", "",
              "| Market | Products | Ingredient list extracted | Allergen statement found | Gluten statement found | "
              "Any statement found |", "|---|---|---|---|---|---|"]
    for mk in MARKETS:
        e = extraction[mk]
        lines.append(f"| {mk} | {e['products']:,} | {pct(e['ingredient_list'], e['products'])} | "
                     f"{pct(e['allergen_statement'], e['ingredient_list'])} | "
                     f"{pct(e['gluten_statement'], e['ingredient_list'])} | {pct(e['any_statement'], e['ingredient_list'])} |")

    lines += ["", "## 2. Allergen detection against reference A", "",
              "Detected = the engine flags the allergen (🔴 or 🟡) for a profile avoiding it.", "",
              "| Market | Allergen | Declared in reference | Detected | Missed (🟢) | Recall | Recall in STRICT |",
              "|---|---|---|---|---|---|---|"]
    tot, tot_strict = Counter(), Counter()
    for (mk, g), c in sorted(allergen.items()):
        n = sum(c.values())
        s = allergen_strict[(mk, g)]
        tot.update(c)
        tot_strict.update(s)
        lines.append(f"| {mk} | {g} | {n} | {c['red'] + c['yellow']} | {c['green']} | {pct(n - c['green'], n)} | "
                     f"{pct(n - s['green'], n)} |")
    n_all = sum(tot.values())
    lines.append(f"| **All** | | **{n_all:,}** | {tot['red'] + tot['yellow']:,} | **{tot['green']}** | "
                 f"**{pct(n_all - tot['green'], n_all)}** | **{pct(n_all - tot_strict['green'], n_all)}** |")

    lines += ["", "## 3. Why each miss happened (failure buckets)", "",
              "Automatic classification with a keyword list independent of the engine's database; the manual review "
              "is in `benchmark-review` and agreed with it.", "",
              "| Bucket | Misses | What it means | Products |", "|---|---|---|---|"]
    by_bucket = defaultdict(list)
    for x in misses:
        by_bucket[x["bucket"]].append(x)
    for key, title, meaning in BUCKETS:
        items = by_bucket.get(key, [])
        names = "; ".join(f'{x["name"][:28] or x["code"]} ({x["group"]}, {x["market"]})' for x in items[:12])
        lines.append(f"| {title} | {len(items)} | {meaning} | {names or '-'} |")

    lines += ["", "## 4. False-alarm proxy: 🔴 for an allergen the reference does not record", "",
              "Not a true false-positive rate: an allergen missing from reference A is not proof of absence (Open Food "
              "Facts tags are incomplete). Each flag is split by whether the independent keyword list sees the "
              "allergen in the text: if it does, the reference is incomplete; if not, it may be an engine false "
              "alarm (or a word the keyword list lacks) and is read by hand.", "",
              "| Allergen | Products without it in the reference | Flagged 🔴 | Named in the text | Not named "
              "(upper bound on false alarms) |", "|---|---|---|---|---|"]
    for g in GROUPS:
        n = sum(not_declared[(mk, g)]["n"] for mk in MARKETS)
        red = sum(not_declared[(mk, g)]["red"] for mk in MARKETS)
        named = sum(not_declared[(mk, g)]["named"] for mk in MARKETS)
        lines.append(f"| {g} | {n:,} | {red:,} ({pct(red, n)}) | {named:,} | {red - named:,} ({pct(red - named, n)}) |")
    tot_n = sum(c["n"] for c in not_declared.values())
    tot_red = sum(c["red"] for c in not_declared.values())
    tot_named = sum(c["named"] for c in not_declared.values())
    lines += [f"| **All** | **{tot_n:,}** | **{tot_red:,}** | **{tot_named:,}** | **{tot_red - tot_named:,} "
              f"({pct(tot_red - tot_named, tot_n)})** |", "",
              "<details>", "<summary>Flags with the allergen not named in the text (first 40)</summary>", "",
              "| Market | Allergen | Product | Why the engine says 🔴 |", "|---|---|---|---|"]
    for mk, g, code, pname, why in alarm_examples[:40]:
        lines.append(f"| {mk} | {g} | {pname[:40]} ({code}) | {why.replace('|', '/')} |")
    lines += ["", "</details>"]

    lines += ["", "## 5. Reference B: the manufacturer's own allergen statement", "",
              "Products whose ingredient text includes an allergen statement. The ingredients are checked again "
              "**without the statement**, so the engine cannot find an allergen by reading the declaration. "
              "Recall: declared allergens the engine flags from the ingredients alone (🔴 or 🟡, as in reference A). "
              "Precision: definite (🔴) flags on allergens the market requires that the statement also declares; "
              "the rest are labels whose statement leaves the allergen out (XC2: a label error or an engine false "
              "alarm, for a person to read).", "",
              "| Market | Products with a statement | Allergens declared | Flagged from the ingredients alone "
              "(recall) | Of which 🔴 | 🔴 flags also declared (precision) | Statements missing a required allergen "
              "(XC2) |", "|---|---|---|---|---|---|---|"]
    for mk in MARKETS:
        b = ref_b[mk]
        lines.append(f"| {mk} | {b['products']:,} | {b['declared']:,} | {b['declared_flagged']:,} "
                     f"({pct(b['declared_flagged'], b['declared'])}) | {b['declared_red']:,} | "
                     f"{b['required_red_declared']:,} of {b['required_red']:,} "
                     f"({pct(b['required_red_declared'], b['required_red'])}) | "
                     f"{b['xc2']:,} ({pct(b['xc2'], b['products'])}) |")
    lines += ["", "<details>", "<summary>Statements missing a required allergen (first 30)</summary>", "",
              "| Market | Product | What XC2 reports | Ingredient text |", "|---|---|---|---|"]
    for mk, code, pname, issue, txt in xc2_examples[:30]:
        lines.append(f"| {mk} | {pname[:36]} ({code}) | {issue.replace('|', '/')} | {txt.replace('|', '/')} |")
    lines += ["", "</details>"]

    lines += ["", "## 6. Claims on the pack vs the engine", "",
              "A 🔴 here means the engine found something that contradicts the claim: an engine false alarm, a "
              "data error or a real labeling issue. Each one needs a person to look.", "",
              "| Market | Claim | Products | 🟢 | 🟡 | 🔴 conflict |", "|---|---|---|---|---|---|"]
    for (mk, name), c in sorted(claims.items()):
        lines.append(f"| {mk} | {name} | {sum(c.values())} | {c['green']} | {c['yellow']} | {c['red']} |")
    lines += ["", "<details>", "<summary>Conflicts (first 30)</summary>", "",
              "| Market | Claim | Product | Why the engine says 🔴 |", "|---|---|---|---|"]
    for mk, name, code, pname, why in claim_conflicts[:30]:
        lines.append(f"| {mk} | {name} | {pname[:40]} ({code}) | {why.replace('|', '/')} |")
    lines += ["", "</details>"]

    lines += ["", "## 7. Coverage: ingredients found in the database", "",
              "| Market | Ingredients | Found | Coverage | Most frequent unknown items |", "|---|---|---|---|---|"]
    for mk in MARKETS:
        f, t = coverage[mk]
        top = ", ".join(f"{k} ({v})" for k, v in unknown[mk].most_common(12))
        lines.append(f"| {mk} | {t:,} | {f:,} | {pct(f, t)} | {top.replace('|', '/')} |")

    lines += ["", "## 8. Metamorphic tests (properties that must hold for any label)", "",
              "| Property | Checks | Failures |", "|---|---|---|"]
    for rel in sorted({rel for rel, _ in meta}):
        ok, bad = meta[(rel, True)], meta[(rel, False)]
        lines.append(f"| {rel} | {ok + bad:,} | {bad} |")
    for rel, fails in meta_fail.items():
        lines += ["", f"Examples of failures, {rel}:"] + [f"- {c} ({a}): {t}" for c, a, t in fails]

    lines += ["", "## 9. Performance", "",
              f"{n_checks:,} engine runs: median {statistics.median(timings):.1f} ms, "
              f"95th percentile {statistics.quantiles(timings, n=20)[18]:.1f} ms per label.", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "rules_version": engine.RULES_VERSION, "data_hash": engine.DATA_HASH, "products": len(products),
        "engine_runs": n_checks, "allergen_checks": n_all, "false_greens": tot["green"],
        "false_green_rate": tot["green"] / n_all if n_all else 0, "false_greens_strict": tot_strict["green"],
        "failure_buckets": {key: len(by_bucket.get(key, [])) for key, _, _ in BUCKETS},
        "extraction": {mk: {k: v for k, v in extraction[mk].items()} for mk in MARKETS},
        "ingredient_list_rate": round(tot_lists / tot_products, 4) if tot_products else 0,
        "reference_b": {mk: dict(ref_b[mk]) for mk in MARKETS},
        "false_alarm_proxy": {g: {k: sum(not_declared[(mk, g)][k] for mk in MARKETS)
                                  for k in ("n", "red", "named", "not_named")} for g in GROUPS},
        "claims": {f"{mk}/{n}": dict(c) for (mk, n), c in claims.items()},
        "coverage": {mk: round(f / t, 4) if t else 0 for mk, (f, t) in coverage.items()},
        "metamorphic_checks": sum(meta.values()),
        "metamorphic_failures": sum(v for (r, ok), v in meta.items() if not ok),
        "misses": misses,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "misses"}, indent=2))


if __name__ == "__main__":
    main()
