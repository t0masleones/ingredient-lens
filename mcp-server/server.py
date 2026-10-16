"""Ingredient Lens MCP server: tools the Claude agent calls instead of guessing."""

from mcp.server.mcpserver import MCPServer

import engine
import review

mcp = MCPServer("ingredient-lens", version=engine.RULES_VERSION)
_matcher = engine.Matcher(engine.connect())


@mcp.tool()
def check_label(label_text: str, avoid: list[str], strict: bool = False, market: str = "BR") -> dict:
    """Classify a transcribed ingredient label or recipe and cross-check its statements.

    Call this after transcribing the label exactly. Base the verdict on the result.

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
                         mismatches: list[str], questions_for_supplier: list[str]) -> dict:
    """Send a case to human review (regulatory or quality expert). Ask the user before calling it.

    Use when check_label returns escalate_to_human_review = true.
    """
    body = "\n".join([
        f"**Verdict:** {verdict}", "", f"**Summary:** {summary}", "",
        "**Mismatches:**", *[f"- {m}" for m in mismatches or ["none"]], "",
        "**Questions for the supplier:**", *[f"- {q}" for q in questions_for_supplier or ["none"]], "",
        "**Label text:**", "```", label_text, "```", "",
        f"_Created by Ingredient Lens rules {engine.RULES_VERSION}. Screening aid, not regulatory advice._",
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
