"""Build data/off-terms.csv from the Open Food Facts taxonomies (additives and ingredients).

Usage: uv run data/import_off.py [folder with additives.json, ingredients.json, additives.txt, ingredients.txt]
Without a folder, the taxonomies are downloaded (JSON from static.openfoodfacts.org, the source .txt files with
synonyms from the openfoodfacts-server repository).

What is imported, and how conservatively:
- Names and synonyms in Portuguese, English and Spanish, plus French, German, Italian and Dutch for EU labels.
  A foreign-language term never replaces a Portuguese, English or Spanish one ("polvo" is octopus in Portuguese
  and powder in Spanish), and short or common words are skipped.
- Diet status (vegan / vegetarian) comes from Open Food Facts, inherited from parent ingredients.
- Allergens are never assumed absent without evidence. An animal allergen (milk, egg, fish, crustacean,
  mollusc) is ruled out only when the ingredient is vegan. Gluten, soy, peanut, tree nuts and sesame are ruled out
  only for fruit, vegetable, herb, spice, salt or water. Celery, mustard, sulphites and lupin are never ruled out
  (dried fruit can hold sulphites, spice mixes mustard or celery). Anything else goes into may_allergens, so the
  rules engine answers 🟡 instead of 🟢.
- Known allergen sources come from the allergens property in the taxonomy, from the parent ingredient (child of
  milk, wheat, soya...) and from the curated terms found in the name ("farinha de trigo integral" inherits gluten).
- Additives are purified substances; label laws (RDC 727/2022, EU 1169/2011) still require declaring an allergen
  source, so only the codes in ADDITIVE_ALLERGENS carry allergen flags.
- Curated rows in ingredients.csv always win: their terms are skipped here.

Data: Open Food Facts taxonomies, © Open Food Facts contributors, Open Database License (ODbL) 1.0.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import engine  # noqa: E402

DATA = Path(__file__).parent
OUT = DATA / "off-terms.csv"
JSON_URL = "https://static.openfoodfacts.org/data/taxonomies/{}.json"
TXT_URL = {"additives": "https://raw.githubusercontent.com/openfoodfacts/openfoodfacts-server/main/taxonomies/additives.txt",
           "ingredients": "https://raw.githubusercontent.com/openfoodfacts/openfoodfacts-server/main/taxonomies/food/ingredients.txt"}
BASE_LANGS = ("pt", "en", "es")
EU_LANGS = ("fr", "de", "it", "nl")
FIELDS = ["term", "lang", "lactose", "gluten", "allergens", "may_allergens", "origin", "animal_type", "note", "source"]
# Common words in the base languages that are also food words elsewhere ("mais" is maize in German).
STOPWORDS = {"mais", "para", "com", "sem", "pode", "conter", "todo", "toda", "como", "the", "and", "with", "from",
             "sal", "sel", "pan", "pane", "brot", "agua", "rosa", "pera", "lima", "data", "mate", "cola", "base",
             "gras", "fino", "fina", "real", "nata", "alle", "eine", "ohne", "sans", "avec", "cream", "cafe"}

ANIMAL_GROUPS = {"milk", "egg", "fish", "crustacean", "mollusc"}
PLANT_GROUPS = {"gluten", "soy", "peanut", "tree_nuts", "sesame"}
EU_ONLY_GROUPS = {"celery", "mustard", "sulphites", "lupin"}
# "en:shellfish" is left out on purpose: it groups crustaceans and molluscs, which are separate allergens.
ALLERGEN_PARENTS = {
    "en:dairy": "milk", "en:milk": "milk", "en:egg": "egg", "en:fish": "fish", "en:crustacean": "crustacean",
    "en:mollusc": "mollusc", "en:wheat": "gluten", "en:barley": "gluten",
    "en:rye": "gluten", "en:oat": "gluten", "en:spelt": "gluten", "en:gluten": "gluten", "en:soya": "soy",
    "en:peanut": "peanut", "en:nut": "tree_nuts", "en:tree-nut": "tree_nuts", "en:sesame": "sesame",
    "en:celery": "celery", "en:mustard": "mustard", "en:lupin": "lupin",
}
OFF_ALLERGENS = {"en:milk": "milk", "en:eggs": "egg", "en:fish": "fish", "en:crustaceans": "crustacean",
                 "en:molluscs": "mollusc", "en:gluten": "gluten", "en:soybeans": "soy", "en:peanuts": "peanut",
                 "en:nuts": "tree_nuts", "en:sesame-seeds": "sesame", "en:celery": "celery", "en:mustard": "mustard",
                 "en:lupin": "lupin", "en:sulphur-dioxide-and-sulphites": "sulphites"}
SAFE_PARENTS = {"en:fruit", "en:vegetable", "en:herb", "en:spice", "en:salt", "en:water"}
NON_GLUTEN_CEREALS = {"en:corn", "en:rice", "en:buckwheat", "en:quinoa", "en:millet", "en:sorghum", "en:teff",
                      "en:amaranth"}
# Additives that can come from an allergen. (allergens, may_allergens, lactose)
ADDITIVE_ALLERGENS = {
    "e322": ("", "soy;egg", ""),                       # lecithins: soy, sunflower or egg
    "e1105": ("egg", "", ""),                          # lysozyme is made from egg white
    "e966": ("", "milk", "yellow"),                    # lactitol is made from lactose
    **{f"e{n}": ("", "gluten", "") for n in (1404, 1410, 1412, 1413, 1414, 1420, 1422, 1440, 1442, 1450, 1451, 1452)},
    **{f"e{n}": ("sulphites", "", "") for n in range(220, 229)},
}
# Open Food Facts marks sugars "maybe vegan" because of bone-char filtering. The origin glossary treats that as an
# invisible processing aid (sugar is plant-based, with a note), so the curated policy wins.
DIET_OVERRIDES = {"en:sugar": ("yes", "yes", "Some cane sugar is filtered with bone char (not visible on the label)")}
VEGETARIAN_TYPE = {"no": "slaughter", "yes": "non_slaughter", "maybe": "maybe_slaughter"}
RANK = {"non_animal": 0, "either": 1, "animal": 2}


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as resp:
        return resp.read()


def load(folder: Path | None, name: str) -> tuple[dict, str]:
    if folder:
        return (json.loads((folder / f"{name}.json").read_text(encoding="utf-8")),
                (folder / f"{name}.txt").read_text(encoding="utf-8"))
    return json.loads(fetch(JSON_URL.format(name))), fetch(TXT_URL[name]).decode("utf-8")


def parse_txt(txt: str, tax: dict) -> dict[str, dict]:
    """Synonyms per language and the allergens property, per taxonomy key."""
    index = {(lang, engine.normalize(name)): key for key, e in tax.items() for lang, name in e.get("name", {}).items()}
    out = {}
    for block in re.split(r"\n\s*\n", txt):
        syns, allergens, key = {}, set(), None
        for line in block.splitlines():
            if m := re.match(r"^([a-z]{2}):\s*(.+)$", line):
                names = [s.strip() for s in m[2].split(",") if s.strip()]
                syns.setdefault(m[1], []).extend(names)
                if key is None and names:
                    first = engine.normalize(names[0])
                    key = (f"en:{first.replace(' ', '')}" if re.fullmatch(r"e ?\d{3,4}[a-z]*", first) else None) \
                        or index.get((m[1], first)) or f"{m[1]}:{first.replace(' ', '-')}"
            elif m := re.match(r"^allergens:en:\s*(.+)$", line):
                allergens |= {OFF_ALLERGENS[a.strip()] for a in m[1].split(",") if a.strip() in OFF_ALLERGENS}
        if key in tax:
            out[key] = {"synonyms": syns, "allergens": allergens}
    return out


def ancestors(tax: dict, key: str) -> list[str]:
    """Key itself first, then parents breadth-first."""
    seen, queue = [], [key]
    while queue:
        k = queue.pop(0)
        if k not in seen:
            seen.append(k)
            queue += tax.get(k, {}).get("parents", [])
    return seen


def inherited(tax: dict, chain: list[str], prop: str) -> str:
    for k in chain:
        if value := tax.get(k, {}).get(prop, {}).get("en"):
            return value
    return ""


def diet_fields(vegan: str, vegetarian: str) -> tuple[str, str] | None:
    if vegan == "yes":
        return "non_animal", ""
    if vegan == "maybe":
        return "either", ""
    if vegan == "no":
        return "animal", VEGETARIAN_TYPE.get(vegetarian, "maybe_slaughter")
    return None


def names(entry: dict, extra: dict) -> list[tuple[str, str]]:
    """(lang, name) pairs: the main name and the synonyms, in the base and EU languages."""
    out = []
    for lang in BASE_LANGS + EU_LANGS:
        for name in [entry.get("name", {}).get(lang)] + extra.get("synonyms", {}).get(lang, []):
            if name:
                out.append((lang, name.split(" - ", 1)[-1] if re.match(r"^E\d", name) else name))
    return out


def usable(term: str, lang: str) -> bool:
    if len(term) < 3 or re.search(r"[%()\d]", term):
        return False
    return lang in BASE_LANGS or (len(term) >= 4 and term not in STOPWORDS)


def additive_rows(tax: dict, extra: dict) -> list[dict]:
    rows = []
    for key, entry in tax.items():
        code = key.split(":", 1)[1]
        m = re.fullmatch(r"e(\d{3,4})([a-z]*)", code)
        if not m:
            continue
        diet = diet_fields(entry.get("vegan", {}).get("en", ""), entry.get("vegetarian", {}).get("en", ""))
        if not diet:
            continue
        allergens, may, lactose = ADDITIVE_ALLERGENS.get(code, ("", "", ""))
        base = {"lactose": lactose, "gluten": "", "allergens": allergens, "may_allergens": may,
                "origin": diet[0], "animal_type": diet[1], "note": f"Additive {code.upper()} (INS {m[1]}{m[2]})",
                "source": f"openfoodfacts:{key}"}
        number = m[1] + m[2]
        for term in {f"e{number}", f"e {number}", f"ins {number}", f"ins{number}"}:
            rows.append({**base, "term": term, "lang": "xx"})
        for lang, name in names(entry, extra.get(key, {})):
            if usable(engine.normalize(name), lang):
                rows.append({**base, "term": name, "lang": lang})
    return rows


def ingredient_rows(tax: dict, extra: dict, matcher: engine.Matcher) -> list[dict]:
    rows = []
    for key, entry in tax.items():
        chain = ancestors(tax, key)
        vegan, vegetarian = inherited(tax, chain, "vegan"), inherited(tax, chain, "vegetarian")
        override = next((DIET_OVERRIDES[k] for k in chain if k in DIET_OVERRIDES), None)
        if override and vegan in ("maybe", ""):
            vegan, vegetarian = override[:2]
        all_names = names(entry, extra.get(key, {}))
        found = {ALLERGEN_PARENTS[k] for k in chain if k in ALLERGEN_PARENTS}
        if "en:peanut" in chain:
            # Open Food Facts files peanuts under nuts; for labeling, a peanut is a legume, not a tree nut.
            found.discard("tree_nuts")
        for k in chain:
            found |= extra.get(k, {}).get("allergens", set())
        curated = [t for lang, n in all_names if lang in BASE_LANGS for t in matcher.find(n)]
        if vegan == "yes":
            # "nata de coco" holds the dairy word "nata", but a vegan ingredient cannot hold milk, egg or fish.
            curated = [t for t in curated if t.origin != "animal" and not t.allergens & ANIMAL_GROUPS]
        # A name that says "gluten free" or "sin gluten" holds the word, not the allergen.
        curated = [t for t in curated if not (t.term == "gluten" and engine.GLUTEN_FREE.search(
            " ".join(engine.normalize(n) for _, n in all_names)))]
        from_names = set()
        for t in curated:
            from_names |= t.allergens & engine.ALLERGEN_GROUPS
        if NON_GLUTEN_CEREALS & set(chain) and "gluten" not in found:
            # "corn semolina", "sémola de maíz": semolina is the grind here, not wheat.
            from_names.discard("gluten")
        found |= from_names
        diet = diet_fields(vegan, vegetarian)
        if not diet and not found:
            continue
        origin, animal_type = diet or ("either", "")
        safe = set()
        if vegan == "yes":
            safe |= ANIMAL_GROUPS
        if SAFE_PARENTS & set(chain):
            safe |= PLANT_GROUPS
        may = (ANIMAL_GROUPS | PLANT_GROUPS | EU_ONLY_GROUPS) - safe - found
        lactose = engine.worst(*(t.lactose or "green" for t in curated)) if curated else ""
        if "milk" in found:
            lactose = engine.worst(lactose or "green", "yellow" if curated else "red")
        elif "milk" in may:
            lactose = engine.worst(lactose or "green", "yellow")
        gluten = "red" if "gluten" in found else ("yellow" if "gluten" in may else "")
        base = {"lactose": lactose if lactose != "green" else "", "gluten": gluten,
                "allergens": ";".join(sorted(found)), "may_allergens": ";".join(sorted(may)),
                "origin": origin, "animal_type": animal_type,
                "note": "; ".join(n for n in (
                    override[2] if override else "",
                    "may be animal- or plant-derived" if origin == "either" else "",
                    "allergens not verified (Open Food Facts term)" if may - EU_ONLY_GROUPS else "") if n),
                "source": f"openfoodfacts:{key}"}
        for lang, name in all_names:
            if usable(engine.normalize(name), lang):
                rows.append({**base, "term": name, "lang": lang})
    return rows


def merge(rows: list[dict], skip: set[str]) -> list[dict]:
    """One row per normalized term. Base-language rows go first and foreign rows never replace them; when two
    entries in the same tier disagree, keep the more cautious one."""
    out: dict[str, dict] = {}
    base_terms = set()
    for r in sorted(rows, key=lambda r: r["lang"] not in BASE_LANGS + ("xx",)):
        term = engine.normalize(r["term"])
        foreign = r["lang"] not in BASE_LANGS + ("xx",)
        if term in skip or (foreign and term in base_terms):
            continue
        r = {**r, "term": term}
        if not foreign:
            base_terms.add(term)
        old = out.get(term)
        if old is None:
            out[term] = r
            continue
        if RANK[r["origin"]] > RANK[old["origin"]]:
            old["origin"], old["animal_type"] = r["origin"], r["animal_type"]
        for f in ("allergens", "may_allergens"):
            old[f] = ";".join(sorted({x for x in (old[f] + ";" + r[f]).split(";") if x}))
        old["may_allergens"] = ";".join(x for x in old["may_allergens"].split(";")
                                        if x and x not in old["allergens"].split(";"))
        for f in ("lactose", "gluten"):
            old[f] = engine.worst(old[f] or "green", r[f] or "green").replace("green", "")
    return sorted(out.values(), key=lambda r: r["term"])


def main() -> None:
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    matcher = engine.Matcher(sources="curated")
    add_tax, add_txt = load(folder, "additives")
    ing_tax, ing_txt = load(folder, "ingredients")
    rows = additive_rows(add_tax, parse_txt(add_txt, add_tax)) + \
        ingredient_rows(ing_tax, parse_txt(ing_txt, ing_tax), matcher)
    rows = merge(rows, set(matcher.terms))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    langs = {}
    for r in rows:
        langs[r["lang"]] = langs.get(r["lang"], 0) + 1
    print(f"{len(rows)} terms written to {OUT.name}: {dict(sorted(langs.items()))}")


if __name__ == "__main__":
    main()
