"""lookup_ingredient says how each row matched, so a partial match is never read as the answer."""

import engine


def test_exact_and_partial_matches_are_labelled():
    rows = engine.lookup("sal")
    assert rows and rows[0]["match_type"] == "exact"
    partial = [r for r in rows if r["match_type"] == "partial"]
    assert all("Do not use it as the answer" in r["match_note"] for r in partial)


def test_unknown_term_returns_nothing():
    assert all(r["match_type"] == "partial" for r in engine.lookup("zzqx ingrediente inexistente"))
