"""Deterministic rules engine for Ingredient Lens.

The LLM transcribes the label and talks to the user. This module does the parts
that must give the same answer every time: matching ingredients against the
ingredient database, applying the profile, and cross-checking label statements.
"""

from __future__ import annotations

import csv
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

RULES_VERSION = "0.2.0"
DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "ingredients.csv"
DB_PATH = DATA_DIR / "ingredients.db"

RANK = {"green": 0, "yellow": 1, "red": 2}
ALLERGEN_GROUPS = {"milk", "egg", "soy", "peanut", "tree_nuts", "sesame", "fish", "crustacean", "mollusc", "gluten"}
DIETS = {"vegan", "vegetarian"}
AVOID_ALIASES = {"wheat": "gluten", "celiac": "gluten", "nuts": "tree_nuts", "tree nuts": "tree_nuts",
                 "peanuts": "peanut", "shellfish": "crustacean", "eggs": "egg"}
VEGETARIAN_RED = {"meat", "fish", "slaughter"}
VEGETARIAN_YELLOW = {"insect", "dairy_rennet"}


def normalize(text: str) -> str:
    """Lowercase, strip accents, turn hyphens into spaces, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = re.sub(r"[‐-―-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def worst(*levels: str) -> str:
    return max(levels, key=RANK.__getitem__, default="green")


# ---------------------------------------------------------------- database

def build_db(csv_path: Path = CSV_PATH, db_path: Path = DB_PATH) -> Path:
    """(Re)build the SQLite ingredient master from the versioned CSV."""
    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("""CREATE TABLE ingredient (
        term TEXT PRIMARY KEY, lang TEXT, lactose TEXT, gluten TEXT, allergens TEXT,
        may_allergens TEXT, origin TEXT, animal_type TEXT, note TEXT, source TEXT)""")
    with open(csv_path, encoding="utf-8", newline="") as f:
        rows = [{**r, "term": normalize(r["term"])} for r in csv.DictReader(f)]
    con.executemany("""INSERT INTO ingredient VALUES (:term, :lang, :lactose, :gluten, :allergens,
        :may_allergens, :origin, :animal_type, :note, :source)""", rows)
    con.commit()
    con.close()
    return db_path


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists() or DB_PATH.stat().st_mtime < CSV_PATH.stat().st_mtime:
        build_db()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


@dataclass
class Term:
    term: str
    lactose: str
    gluten: str
    allergens: set[str]
    may_allergens: set[str]
    origin: str
    animal_type: str
    note: str
    source: str

    @classmethod
    def from_row(cls, r: sqlite3.Row) -> "Term":
        split = lambda s: {x for x in (s or "").split(";") if x}
        allergens = split(r["allergens"])
        if r["gluten"] == "red":
            allergens.add("gluten")
        return cls(r["term"], r["lactose"] or "", r["gluten"] or "", allergens, split(r["may_allergens"]),
                   r["origin"], r["animal_type"] or "", r["note"] or "", r["source"])


class Matcher:
    """Longest-match term finder over normalized text (allows a plural s/es)."""

    def __init__(self, con: sqlite3.Connection):
        self.terms = {r["term"]: Term.from_row(r) for r in con.execute("SELECT * FROM ingredient")}
        alternation = "|".join(re.escape(t) for t in sorted(self.terms, key=len, reverse=True))
        self.pattern = re.compile(rf"\b({alternation})(?:s|es)?\b")
        self.data_version = con.execute("SELECT COUNT(*) FROM ingredient").fetchone()[0]

    def find(self, text: str) -> list[Term]:
        return [self.terms[m.group(1)] for m in self.pattern.finditer(normalize(text))]


# ---------------------------------------------------------------- parsing

HEADER = re.compile(r"\b(ingredientes|ingredients)\s*:", re.I)
STATEMENT_START = re.compile(
    r"\b(alergicos|alergenos|allergens|contem|contains|contiene|pode conter|may contain|puede contener|"
    r"nao contem|zero lactose|sem lactose|lactose free|gluten free|sem gluten|sin gluten|vegano|vegan)\b")
GLUTEN_FREE = re.compile(r"\b(nao contem gluten|sem gluten|isento de gluten|gluten free|sin gluten|libre de gluten)\b")
GLUTEN_CONTAINS = re.compile(r"\b(contem gluten|contains gluten|contiene gluten)\b")
LACTOSE_FREE = re.compile(r"(\bzero lactose|\bsem lactose|\bisento de lactose|0% lactose|\bnao contem lactose|"
                          r"\blactose free|\bsin lactosa)\b")
LACTOSE_CONTAINS = re.compile(r"\b(contem lactose|contains lactose|contiene lactosa)\b")
VEGAN_CLAIM = re.compile(r"\b(vegano|vegana|vegan|100% vegetal|plant based)\b")
VEGETARIAN_CLAIM = re.compile(r"\b(vegetariano|vegetariana|vegetarian)\b")
MAY_CONTAIN = re.compile(r"\b(pode conter|may contain|puede contener)\b")
CONTAINS = re.compile(r"\b(contem|contains|contiene)\b")


def split_top_level(text: str) -> list[str]:
    """Split on commas/semicolons/newlines that are not inside parentheses."""
    parts, depth, buf = [], 0, []
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(depth - 1, 0)
        if depth == 0 and ch in ",;\n":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [p.strip(" .") for p in parts if p.strip(" .")]


def split_ingredients(list_text: str) -> list[str]:
    """Flatten 'A, B (b1, b2), C' into ['A', 'B', 'b1', 'b2', 'C']."""
    out = []
    for item in split_top_level(list_text):
        m = re.match(r"^(.*?)\((.*)\)\s*(.*)$", item, re.S)
        if m:
            head = f"{m.group(1)} {m.group(3)}".strip()
            if head:
                out.append(head)
            out.extend(split_ingredients(m.group(2)))
        else:
            out.append(item)
    return out


@dataclass
class Statements:
    allergen_statement_found: bool = False
    contains: set[str] = field(default_factory=set)
    may_contain: set[str] = field(default_factory=set)
    gluten: str = "not found"       # "contains", "free", "not found"
    lactose: str = "not found"      # "contains", "free", "not found"
    vegan_claim: bool = False
    vegetarian_claim: bool = False
    raw: str = ""


def parse_label(text: str, matcher: Matcher) -> tuple[list[str], Statements]:
    """Return (ingredient items, statements). Recipes without a header are all ingredients."""
    header = HEADER.search(text)
    if header:
        body = text[header.end():]
        # The list ends at the first statement keyword or the first sentence end, whichever comes first.
        ends = [m.start() for m in (STATEMENT_START.search(normalize_keep_len(body)), re.search(r"\.(\s|$)", body)) if m]
        cut = min(ends, default=len(body))
        list_text, rest = body[:cut], text[:header.start()] + " " + body[cut:]
    else:
        # A recipe such as "Pastry for vegan guests: flour; lard; salt" -> drop the title.
        title = re.match(r"^[^:;\n]{0,100}:\s*", text)
        list_text, rest = (text[title.end():] if title else text), ""
    return split_ingredients(list_text), parse_statements(rest, matcher)


def normalize_keep_len(text: str) -> str:
    """Accent-strip and lowercase one character at a time, keeping offsets aligned."""
    out = []
    for ch in text:
        base = "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c))
        out.append((base or ch)[0].lower())
    return "".join(out)


def groups_in(text: str, matcher: Matcher) -> set[str]:
    groups = set()
    for t in matcher.find(text):
        groups |= t.allergens & ALLERGEN_GROUPS
    return groups


def parse_statements(text: str, matcher: Matcher) -> Statements:
    st = Statements(raw=text.strip())
    norm = normalize(text)
    if GLUTEN_FREE.search(norm):
        st.gluten = "free"
    elif GLUTEN_CONTAINS.search(norm):
        st.gluten = "contains"
    if LACTOSE_FREE.search(norm):
        st.lactose = "free"
    elif LACTOSE_CONTAINS.search(norm):
        st.lactose = "contains"
    st.vegan_claim = bool(VEGAN_CLAIM.search(norm))
    st.vegetarian_claim = bool(VEGETARIAN_CLAIM.search(norm))

    # Remove the gluten/lactose claims so "não contém glúten" is not read as an allergen.
    norm = GLUTEN_FREE.sub(" ", LACTOSE_FREE.sub(" ", LACTOSE_CONTAINS.sub(" ", norm)))
    for sentence in re.split(r"[.!]", norm):
        may = MAY_CONTAIN.search(sentence)
        head, tail = (sentence[:may.start()], sentence[may.end():]) if may else (sentence, "")
        if tail:
            st.allergen_statement_found = True
            st.may_contain |= groups_in(tail, matcher)
        has = CONTAINS.search(head)
        if has:
            if re.search(r"\b(alergicos|alergenos|allergens|contains|contiene|derivados)\b", head):
                st.allergen_statement_found = True
            st.contains |= groups_in(head[has.end():], matcher)
    return st


# ---------------------------------------------------------------- checking

def normalize_avoid(avoid: list[str]) -> list[str]:
    out = []
    for a in avoid:
        a = normalize(a).replace("-", " ")
        a = AVOID_ALIASES.get(a, a.replace(" ", "_"))
        if a not in out:
            out.append(a)
    return out


def status_for(term: Term, avoid: str, lactose_free_with_lactase: bool) -> tuple[str, str]:
    """Status of one matched term for one restriction, plus a short reason."""
    if avoid == "lactose":
        level = term.lactose or "green"
        if level != "green" and lactose_free_with_lactase and "milk" in term.allergens:
            return "green", "lactose-free claim and lactase listed"
        return level, term.note if level != "green" else ""
    if avoid == "vegan":
        if term.origin == "animal":
            return "red", f"animal-derived ({term.animal_type})"
        if term.origin in ("either", "unknown"):
            return "yellow", f"can be either: {term.note}".rstrip(": ")
        return "green", ""
    if avoid == "vegetarian":
        if term.origin == "animal" and term.animal_type in VEGETARIAN_RED:
            return "red", f"animal-derived ({term.animal_type})"
        if term.origin == "animal" and term.animal_type in VEGETARIAN_YELLOW:
            return "yellow", term.note
        if term.origin in ("either", "unknown"):
            return "yellow", f"can be either: {term.note}".rstrip(": ")
        return "green", ""
    if avoid == "gluten" and term.gluten:
        return term.gluten, term.note if term.gluten != "green" else ""
    if avoid == "milk" and term.lactose == "yellow" and "milk" not in term.allergens:
        return "yellow", term.note
    if avoid in term.allergens:
        return "red", f"contains {avoid}"
    if avoid in term.may_allergens:
        return "yellow", f"source not stated; may contain {avoid}"
    return "green", ""


def check_label(label_text: str, avoid: list[str], strict: bool = False, market: str = "BR",
                matcher: Matcher | None = None) -> dict:
    """Classify a transcribed label or recipe against a profile and cross-check its statements."""
    matcher = matcher or Matcher(connect())
    avoid = normalize_avoid(avoid)
    items, st = parse_label(label_text, matcher)
    if not items:
        return {"rules_version": RULES_VERSION, "verdict": "insufficient",
                "reason": "No ingredient list found. Ask for a photo of the ingredient panel or the list."}

    matched = [(item, matcher.find(item)) for item in items]
    terms = [t for _, ts in matched for t in ts]
    has_lactase = any(t.term == "lactase" for t in terms)
    lactose_free_with_lactase = st.lactose == "free" and has_lactase

    ingredients, findings = [], []
    for item, ts in matched:
        entry = {"text": item, "matched_terms": [t.term for t in ts],
                 "origin": "unknown" if not ts else _merge_origin(ts), "status": {}, "notes": []}
        for t in ts:
            if t.note and t.note not in entry["notes"]:
                entry["notes"].append(t.note)
        for a in avoid:
            if not ts:
                level, why = "yellow", "not in the ingredient database; check it"
            else:
                pairs = [status_for(t, a, lactose_free_with_lactase) for t in ts]
                level = worst(*(p[0] for p in pairs))
                why = "; ".join(sorted({p[1] for p in pairs if p[0] == level and p[1]}))
            if strict and level == "yellow" and a not in DIETS:
                level, why = "red", f"STRICT mode: {why}"
            entry["status"][a] = level
            if level != "green":
                findings.append({"ingredient": item, "restriction": a, "level": level, "why": why})
        ingredients.append(entry)

    findings += _statement_findings(st, avoid, strict)
    mismatches = _cross_check(st, terms, has_lactase)

    verdict = worst(*(f["level"] for f in findings)) if findings else "green"
    if mismatches:
        verdict = worst(verdict, "red" if strict else "yellow")
    notes = []
    if market.upper() == "BR" and st.gluten == "not found" and ("gluten" in avoid or not avoid):
        notes.append("No CONTÉM GLÚTEN / NÃO CONTÉM GLÚTEN statement found (required in Brazil by Lei 10.674/2003).")
    if any(t.allergens - {"gluten"} for t in terms) and not st.allergen_statement_found:
        notes.append("No allergen statement found in the text provided.")
    if set(avoid) & DIETS:
        notes.append("Processing aids and cross-contact are usually not visible on a label.")
    unknown = sum(1 for _, ts in matched if not ts)
    return {
        "rules_version": RULES_VERSION,
        "data_version": f"{matcher.data_version} terms",
        "market": market.upper(),
        "mode": "STRICT" if strict else ("DIET" if set(avoid) <= DIETS and avoid else "INFORMATIVE"),
        "profile": avoid,
        "verdict": verdict,
        "escalate_to_human_review": bool(mismatches) or (strict and verdict != "green"),
        "coverage": f"{len(items) - unknown}/{len(items)} ingredients found in the database",
        "ingredients": ingredients,
        "statements": {"allergen_statement_found": st.allergen_statement_found,
                       "contains": sorted(st.contains), "may_contain": sorted(st.may_contain),
                       "gluten": st.gluten, "lactose": st.lactose,
                       "vegan_claim": st.vegan_claim, "vegetarian_claim": st.vegetarian_claim},
        "findings": findings,
        "mismatches": mismatches,
        "notes": notes,
    }


def _merge_origin(ts: list[Term]) -> str:
    origins = {t.origin for t in ts}
    for o in ("animal", "either", "unknown"):
        if o in origins:
            return o
    return sorted(origins)[0]


def _statement_findings(st: Statements, avoid: list[str], strict: bool) -> list[dict]:
    out = []
    for a in avoid:
        groups = {"lactose": {"milk"}, "vegan": {"milk", "egg", "fish", "crustacean", "mollusc"},
                  "vegetarian": {"fish", "crustacean", "mollusc"}}.get(a, {a})
        # A zero-lactose claim settles lactose for the milk declaration (XC3 catches it when lactase is missing).
        if st.contains & groups and not (a == "lactose" and st.lactose == "free"):
            out.append({"ingredient": "allergen statement", "restriction": a, "level": "red",
                        "why": f"label declares: contains {', '.join(sorted(st.contains & groups))}"})
        if st.may_contain & groups:
            level = "red" if strict and a not in DIETS else "yellow"
            out.append({"ingredient": "may-contain statement", "restriction": a, "level": level,
                        "why": f"possible traces: {', '.join(sorted(st.may_contain & groups))}"})
    return out


def _cross_check(st: Statements, terms: list[Term], has_lactase: bool) -> list[dict]:
    out = []
    gluten_terms = sorted({t.term for t in terms if t.gluten == "red"})
    if st.gluten == "free" and (gluten_terms or "gluten" in st.contains | st.may_contain):
        out.append({"rule": "XC1", "issue": "Label says NÃO CONTÉM GLÚTEN / gluten free, but lists or may contain "
                    f"a gluten source: {', '.join(gluten_terms) or 'see allergen statement'}."})
    if st.allergen_statement_found:
        listed = {g for t in terms for g in t.allergens if g in ALLERGEN_GROUPS}
        missing = sorted(listed - st.contains - st.may_contain)
        if missing:
            out.append({"rule": "XC2", "issue": f"Ingredients include {', '.join(missing)}, "
                        "but the allergen statement does not declare it."})
    if st.lactose == "free" and not has_lactase:
        dairy = sorted({t.term for t in terms if t.lactose == "red"})
        if dairy:
            out.append({"rule": "XC3", "issue": f"Zero-lactose claim, but {', '.join(dairy)} listed and no lactase."})
    if st.vegan_claim:
        animal = sorted({t.term for t in terms if t.origin == "animal"} |
                        (st.contains & {"milk", "egg", "fish", "crustacean", "mollusc"}))
        if animal:
            out.append({"rule": "XC4", "issue": f"Vegan claim, but animal-derived items found: {', '.join(animal)}."})
    return out


def lookup(name: str, con: sqlite3.Connection | None = None) -> list[dict]:
    """Exact and partial matches for one ingredient name, straight from SQL."""
    con = con or connect()
    key = normalize(name)
    rows = con.execute(
        "SELECT * FROM ingredient WHERE term = ? OR term LIKE ? OR ? LIKE '%' || term || '%' "
        "ORDER BY term = ? DESC, length(term) DESC LIMIT 10", (key, f"%{key}%", key, key)).fetchall()
    return [dict(r) for r in rows]
