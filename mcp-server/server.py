"""Ingredient Lens MCP server: tools the Claude agent calls instead of guessing."""

from mcp.server.mcpserver import MCPServer

import engine
import review

mcp = MCPServer("ingredient-lens", version=engine.RULES_VERSION)
_matcher = engine.Matcher()


@mcp.tool()
def check_label(label_text: str, avoid: list[str], strict: bool = False, market: str = "BR") -> dict:
    """Classify a transcribed ingredient label or recipe and cross-check its statements.

    Call this after transcribing the label exactly. Base the verdict on the result.
    Include the user's own words when they describe symptoms: a verdict of "urgent" means stop and tell them to
    seek emergency help. Use `wording` instead of ever calling a product safe. In Analyst mode, report the
    `compliance` checklist (pass / fail / review per legal requirement, including GMO labelling and organic or
    other certification claims), the mismatches and the decision in `next_step`: approve, request_evidence (list
    `evidence_needed`) or escalate. The rules screen a label; they never certify it.

    Args:
        label_text: The label text as printed (ingredient list plus allergen, gluten,
            lactose and diet statements), or a recipe's ingredient list.
        avoid: Restrictions, any of: lactose, milk, gluten, egg, soy, peanut, tree_nuts,
            sesame, fish, crustacean, mollusc, vegan, vegetarian. Empty list = analyst
            cross-check only.
        strict: True for an allergy or celiac disease (every unclear item becomes red).
        market: Label market: BR, US or EU.
    """
    result = engine.check_label(label_text, avoid, strict, market, matcher=_matcher)
    review.audit("check_label", {"avoid": avoid, "strict": strict, "market": market,
                                 "label_chars": len(label_text)}, result)
    return result


@mcp.tool()
def lookup_ingredient(name: str) -> list[dict]:
    """Look up one ingredient in the ingredient database (lactose, gluten, allergens, origin, source).

    Use it to explain a single term or to check whether a term is covered.
    """
    rows = engine.lookup(name)
    review.audit("lookup_ingredient", {"name": name}, {"coverage": f"{len(rows)} rows"})
    return rows or [{"term": name, "found": False,
                     "note": "Not in the database. Reason from the label and mark it unclear."}]


@mcp.tool()
def create_review_ticket(title: str, summary: str, label_text: str, verdict: str,
                         mismatches: list[str], questions_for_supplier: list[str],
                         market: str = "", product: str = "", supplier: str = "", lot_or_batch: str = "",
                         artwork_version: str = "", failed_checks: list[str] | None = None) -> dict:
    """Send a case to human review (regulatory or quality expert). Ask the user before calling it.

    Use when check_label returns escalate_to_human_review = true, or a compliance check fails.
    Fill the traceability fields the user gave (product, supplier, lot or batch, artwork version): a reviewer
    must be able to trace the decision to the exact label and lot, as food safety schemes expect.
    """
    trace = [f"- {k}: {v}" for k, v in (("Market", market), ("Product", product), ("Supplier", supplier),
                                         ("Lot or batch", lot_or_batch), ("Artwork version", artwork_version)) if v]
    body = "\n".join([
        f"**Verdict:** {verdict}", "", f"**Summary:** {summary}", "",
        "**Traceability:**", *(trace or ["- not given"]), "",
        "**Failed or review checks:**", *[f"- {c}" for c in failed_checks or ["none"]], "",
        "**Mismatches:**", *[f"- {m}" for m in mismatches or ["none"]], "",
        "**Questions for the supplier:**", *[f"- {q}" for q in questions_for_supplier or ["none"]], "",
        "**Label text:**", "```", label_text, "```", "",
        f"_Created by Ingredient Lens rules {engine.RULES_VERSION}, data {_matcher.data_version}. First-pass "
        "screening, not certification or regulatory advice; certification is done only by accredited bodies._",
    ])
    result = review.create_ticket(f"[Review] {title}", body)
    review.audit("create_review_ticket", {"title": title, "verdict": verdict}, result)
    return result


@mcp.tool()
def usage_stats() -> dict:
    """Usage and quality metrics from the audit log: checks, verdict mix, escalation rate, tickets."""
    return review.usage_stats()


if __name__ == "__main__":
    mcp.run()
