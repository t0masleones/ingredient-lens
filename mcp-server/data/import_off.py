"""Build data/off-terms.csv from the Open Food Facts taxonomies (additives and ingredients).

Usage: uv run data/import_off.py [folder with additives.json and ingredients.json]
Without a folder, the taxonomies are downloaded from static.openfoodfacts.org.

What is imported, and how conservatively:
- Diet status (vegan / vegetarian) comes from Open Food Facts, inherited from parent ingredients.
- Allergens are never assumed absent without evidence. An animal allergen (milk, egg, fish, crustacean,
  mollusc) is ruled out only when the ingredient is vegan. A plant allergen (gluten, soy, peanut, tree nuts,
  sesame) is ruled out only for fruit, vegetable, herb, spice, salt or water. Anything else goes into
  may_allergens, so the rules engine answers 🟡 instead of 🟢.
- Known allergen sources come from the parent ingredient (child of milk, wheat, soya...) and from the curated
  terms found in the name (so "farinha de trigo integral" inherits gluten from "trigo").
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
URL = "https://static.openfoodfacts.org/data/taxonomies/{}.json"
LANGS = ("pt", "en", "es")
FIELDS = ["term", "lang", "lactose", "gluten", "allergens", "may_allergens", "origin", "animal_type", "note", "source"]

ANIMAL_GROUPS = {"milk", "egg", "fish", "crustacean", "mollusc"}
PLANT_GROUPS = {"gluten", "soy", "peanut", "tree_nuts", "sesame"}
ALLERGEN_PARENTS = {
    "en:dairy": "milk", "en:milk": "milk", "en:egg": "egg", "en:fish": "fish", "en:crustacean": "crustacean",
    "en:shellfish": "crustacean", "en:mollusc": "mollusc", "en:wheat": "gluten", "en:barley": "gluten",
    "en:rye": "gluten", "en:oat": "gluten", "en:spelt": "gluten", "en:gluten": "gluten", "en:soya": "soy",
    "en:peanut": "peanut", "en:nut": "tree_nuts", "en:tree-nut": "tree_nuts", "en:sesame": "sesame",
}
SAFE_PARENTS = {"en:fruit", "en:vegetable", "en:herb", "en:spice", "en:salt", "en:water"}
# Additives that can come from an allergen. (allergens, may_allergens, lactose)
ADDITIVE_ALLERGENS = {
    "e322": ("", "soy;egg", ""),                       # lecithins: soy, sunflower or egg
    "e1105": ("egg", "", ""),                          # lysozyme is made from egg white
    "e966": ("", "milk", "yellow"),                    # lactitol is made from lactose
    **{f"e{n}": ("", "gluten", "") for n in (1404, 1410, 1412, 1413, 1414, 1420, 1422, 1440, 1442, 1450, 1451, 1452)},
}
# Open Food Facts marks sugars "maybe vegan" because of bone-char filtering. The origin glossary treats that as an
# invisible processing aid (sugar is plant-based, with a note), so the curated policy wins.
DIET_OVERRIDES = {"en:sugar": ("yes", "yes", "Some cane sugar is filtered with bone char (not visible on the label)")}
VEGETARIAN_TYPE = {"no": "slaughter", "yes": "non_slaughter", "maybe": "maybe_slaughter"}
RANK = {"non_animal": 0, "either": 1, "animal": 2}


def load(folder: Path | None, name: str) -> dict:
    if folder:
        return json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))
    with urllib.request.urlopen(URL.format(name), timeout=120) as resp:
        return json.load(resp)


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


def names(entry: dict) -> list[tuple[str, str]]:
    out = []
    for lang in LANGS:
        name = entry.get("name", {}).get(lang)
        if name:
            out.append((lang, name.split(" - ", 1)[-1] if re.match(r"^E\d", name) else name))
    return out


def usable(term: str) -> bool:
    return len(term) >= 3 and not re.search(r"[%()\d]", term)


def additive_rows(tax: dict) -> list[dict]:
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
        for lang, name in names(entry):
            if usable(engine.normalize(name)):
                rows.append({**base, "term": name, "lang": lang})
    return rows


def ingredient_rows(tax: dict, matcher: engine.Matcher) -> list[dict]:
    rows = []
    for key, entry in tax.items():
        chain = ancestors(tax, key)
        vegan, vegetarian = inherited(tax, chain, "vegan"), inherited(tax, chain, "vegetarian")
        override = next((DIET_OVERRIDES[k] for k in chain if k in DIET_OVERRIDES), None)
        if override and vegan in ("maybe", ""):
            vegan, vegetarian = override[:2]
        found = {ALLERGEN_PARENTS[k] for k in chain if k in ALLERGEN_PARENTS}
        curated = [t for _, n in names(entry) for t in matcher.find(n)]
        for t in curated:
            found |= t.allergens & engine.ALLERGEN_GROUPS
        diet = diet_fields(vegan, vegetarian)
        if not diet and not found:
            continue
        origin, animal_type = diet or ("either", "")
        safe = set()
        if vegan == "yes":
            safe |= ANIMAL_GROUPS
        if SAFE_PARENTS & set(chain):
            safe |= PLANT_GROUPS
        may = (ANIMAL_GROUPS | PLANT_GROUPS) - safe - found
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
                    "allergens not verified (Open Food Facts term)" if may else "") if n),
                "source": f"openfoodfacts:{key}"}
        for lang, name in names(entry):
            if usable(engine.normalize(name)):
                rows.append({**base, "term": name, "lang": lang})
    return rows


def merge(rows: list[dict], skip: set[str]) -> list[dict]:
    """One row per normalized term; when two entries disagree, keep the more cautious one."""
    out: dict[str, dict] = {}
    for r in rows:
        term = engine.normalize(r["term"])
        if term in skip:
            continue
        r = {**r, "term": term}
        old = out.get(term)
        if old is None:
            out[term] = r
            continue
        if RANK[r["origin"]] > RANK[old["origin"]]:
            old["origin"], old["animal_type"] = r["origin"], r["animal_type"]
        for f in ("allergens", "may_allergens"):
            old[f] = ";".join(sorted({x for x in (old[f] + ";" + r[f]).split(";") if x}))
        for f in ("lactose", "gluten"):
            old[f] = engine.worst(old[f] or "green", r[f] or "green").replace("green", "")
    return sorted(out.values(), key=lambda r: r["term"])


def main() -> None:
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    matcher = engine.Matcher(sources="curated")
    curated = set(matcher.terms)
    rows = merge(additive_rows(load(folder, "additives")) + ingredient_rows(load(folder, "ingredients"), matcher), curated)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} terms written to {OUT.name}")


if __name__ == "__main__":
    main()
