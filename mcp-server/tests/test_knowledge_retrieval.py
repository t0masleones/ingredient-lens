"""Retrieval quality of search_knowledge, measured on fixed questions with the passage that answers each one.

recall@3 = share of questions whose answering passage is in the top 3. The threshold is the measured value at the
time it was set (v0.6), so a change that makes retrieval worse fails the build. Questions are in the languages users
write in (PT, EN), and the answer is a section of the knowledge files written by the project, never a guess.
"""

import knowledge
import pytest

CASES = [
    ("gluten statement Brazil", "label-rules-br-us-eu#brazil-labels-usually-in-portuguese/gluten-lei-10-674-2003"),
    ("CONTÉM GLÚTEN obrigatório no Brasil", "label-rules-br-us-eu#brazil-labels-usually-in-portuguese/gluten-lei-10-674-2003"),
    ("é obrigatório declarar transgênico", "standards-and-certifications#gmo-labelling-by-market"),
    ("lactase zero lactose claim", "lactose-gluten-glossary#lactose-and-milk/lactose-free-claims"),
    ("organic seal EU code number", "standards-and-certifications#organic-labelling-by-market"),
    ("which evidence: ISO 17025 lab report or certificate", "standards-and-certifications#evidence-types-to-ask-for"),
    ("US major allergens sesame", "label-rules-br-us-eu#united-states"),
    ("cocoa butter is not dairy", "lactose-gluten-glossary#lactose-and-milk/not-dairy-false-alarms"),
    ("questions for the supplier about natural flavour", "origin-glossary#questions-to-ask-a-supplier-for-each-can-be-either"),
    ("may contain traces cross-contact", "lactose-gluten-glossary#cross-contact-warnings"),
    ("explain celiac disease in plain words", "plain-words-glossary#conditions-and-label-words"),
    ("screening is not certification", "standards-and-certifications#the-core-principle-screening-is-not-certification"),
    ("ingredients that can be animal or plant", "origin-glossary#can-be-either-never-guess-ask-the-supplier-or-check-the-prod"),
    ("EU 14 allergens emphasis", "label-rules-br-us-eu#european-union"),
    # Portuguese questions about English passages (found by the agent evaluation, case K02).
    ("Brasil símbolo T transgênico rotulagem quando obrigatório", "standards-and-certifications#gmo-labelling-by-market"),
    ("selo orgânico SisOrg certificado", "standards-and-certifications#organic-labelling-by-market"),
    ("que evidência pedir ao fornecedor: laudo ou certificado", "standards-and-certifications#evidence-types-to-ask-for"),
]
THRESHOLD = 0.85


def recall_at_3() -> tuple[float, list[str]]:
    misses = [q for q, want in CASES if want not in [r["id"] for r in knowledge.search(q, k=3)]]
    return 1 - len(misses) / len(CASES), misses


def test_every_expected_passage_exists():
    ids = {p.id for p in knowledge.passages()}
    assert all(want in ids for _, want in CASES), [w for _, w in CASES if w not in ids]


def test_recall_at_3_does_not_drop():
    score, misses = recall_at_3()
    assert score >= THRESHOLD, f"recall@3 {score:.2f}; misses: {misses}"


def test_unrelated_question_returns_nothing():
    assert knowledge.search("quantum physics of black holes") == []


def test_passages_carry_what_a_citation_needs():
    for r in knowledge.search("GMO labelling Brazil T symbol"):
        assert r["id"] and r["file"] and r["section"] and r["version"]
    assert any(r["to_verify"] for r in knowledge.search("GMO labelling by market"))   # marked TO VERIFY in the file


@pytest.mark.parametrize("q", ["vinagre", "soro de leite em pó"])
def test_same_query_same_passages(q):
    assert knowledge.search(q) == knowledge.search(q)
