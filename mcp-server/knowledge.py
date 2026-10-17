"""Retrieval over the agent's knowledge files, with a citable id for every passage.

The corpus is small (five Markdown files, about 30 KB), so the Claude Project still holds the files in full; this
module exists for the cases full context does not cover: Claude Desktop or another client with the MCP server but no
project files, and answers that must cite the passage they rest on. Passages are the files' own sections (one
heading and its text), never fragments cut mid-sentence. Ranking is BM25 on accent-free words, so the same query
always returns the same passages; no embeddings, no external service.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from engine import normalize

KNOWLEDGE = Path(__file__).resolve().parent.parent / "agent" / "knowledge"
STOP = set("a an and are as at be by de do da das dos e em for from in is it no not o of on or os para por que the "
           "this to um uma with without quando usar como qual quais precisa deve ser tem".split())
# Users write in Portuguese or Spanish; much of the knowledge is in English. Domain words are expanded to their
# English equivalents before ranking (deterministic, reviewed by hand; add a pair when a test shows a gap).
SYNONYMS = {
    "transgenico": "gmo genetically modified", "transgenicos": "gmo genetically modified", "ogm": "gmo",
    "simbolo": "symbol", "rotulagem": "labelling labeling label", "rotulo": "label", "brasil": "brazil",
    "obrigatorio": "mandatory required", "alergicos": "allergens allergen", "alergenos": "allergens allergen",
    "organico": "organic", "organicos": "organic", "selo": "seal", "certificado": "certificate",
    "certificacao": "certification", "laudo": "lab report", "laboratorio": "laboratory lab",
    "leite": "milk", "ovo": "egg", "trigo": "wheat", "cevada": "barley", "fornecedor": "supplier",
    "evidencia": "evidence", "declaracao": "statement declaration", "contem": "contains",
    "tracos": "traces", "vegano": "vegan", "vegetariano": "vegetarian", "origem": "origin",
    "aroma": "flavour flavor", "aromatizante": "flavouring flavoring", "emulsificante": "emulsifier",
    "corante": "colour colorant", "isento": "free", "livre": "free", "celiaco": "celiac",
    "celiaca": "celiac", "intolerancia": "intolerance", "contaminacao": "contamination cross contact",
    "cruzada": "cross contact", "etiqueta": "label", "leche": "milk", "huevo": "egg",
}


@dataclass(frozen=True)
class Passage:
    id: str              # "label-rules-br-us-eu#brazil/gluten-lei-10674-2003"
    file: str
    heading: str         # "Brazil > Gluten - Lei 10.674/2003"
    text: str
    to_verify: bool      # the passage says something is not yet checked against the official text
    version: str         # the file's own version line ("v0.2")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize(text)).strip("-")[:60]


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", normalize(text)) if t not in STOP and len(t) > 1]


@lru_cache(maxsize=1)
def passages() -> tuple[Passage, ...]:
    out = []
    for f in sorted(KNOWLEDGE.glob("*.md")):
        lines = f.read_text(encoding="utf-8").splitlines()
        title = lines[0].lstrip("# ").strip() if lines else f.stem
        version = (re.search(r"\bv\d+(\.\d+)*\b", title) or re.search(r"$", "")).group(0)
        path, buf, heading = [], [], title

        def flush():
            body = "\n".join(buf).strip()
            if body:
                key = "/".join(_slug(h) for h in path) or "intro"
                out.append(Passage(f"{f.stem}#{key}", f.name, " > ".join(path) or title, body,
                                   "TO VERIFY" in body.upper(), version))

        for line in lines[1:]:
            m = re.match(r"^(#{2,6})\s+(.*)", line)
            if m:
                flush()
                level = len(m.group(1)) - 2
                path[:] = path[:level] + [m.group(2).strip()]
                buf = []
            else:
                buf.append(line)
        flush()
    return tuple(out)


@lru_cache(maxsize=1)
def _index():
    # Section titles name the topic ("Brazil > Gluten - Lei 10.674/2003"), so their words count three times.
    docs = [Counter(_tokens(p.text)) + Counter({t: 3 * c for t, c in Counter(_tokens(p.heading)).items()})
            for p in passages()]
    df = Counter(t for d in docs for t in d)
    avg = sum(sum(d.values()) for d in docs) / max(len(docs), 1)
    return docs, df, avg


def search(query: str, k: int = 3, k1: float = 1.4, b: float = 0.75) -> list[dict]:
    """The k best passages for the query, each with its id to cite. An empty list means the knowledge files do not
    cover the question, which the agent must say rather than answer from memory."""
    docs, df, avg = _index()
    q = _tokens(query)
    expand = {t: {t, *_tokens(SYNONYMS.get(t, ""))} for t in q}
    n = len(docs)
    scored = []
    for p, d in zip(passages(), docs):
        length = sum(d.values())
        terms = {e for t in q for e in expand[t]}
        s = sum(math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) * d[t] * (k1 + 1)
                / (d[t] + k1 * (1 - b + b * length / avg)) for t in terms if t in d)
        # A single shared word is a coincidence, not an answer: a passage must cover a third of the question.
        covered = len({t for t in q if expand[t] & d.keys()}) / max(len(set(q)), 1)
        if s > 0 and covered >= 1 / 3 and not p.id.endswith("#sources"):   # source lists are cited, not answers
            scored.append((s, p))
    scored.sort(key=lambda x: -x[0])
    best = scored[0][0] if scored else 0
    return [{"id": p.id, "file": p.file, "section": p.heading, "version": p.version, "score": round(s, 2),
             "to_verify": p.to_verify, "text": p.text[:1800]}
            for s, p in scored[:k] if s >= 0.25 * best]
