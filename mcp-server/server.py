"""Ingredient Lens MCP server: tools the Claude agent calls instead of guessing."""

from mcp.server.mcpserver import MCPServer

import engine
import knowledge
import review

mcp = MCPServer("ingredient-lens", version=engine.RULES_VERSION)
_matcher = engine.Matcher()


@mcp.tool()
def check_label(label_text: str, avoid: list[str], strict: bool = False, market: str = "BR",
                source: str = "text", transcription_confidence: str = "high", complete_pack: bool = True) -> dict:
    """Classify a transcribed ingredient label or recipe and cross-check its statements.

    Call this after transcribing the label exactly. Base the verdict on the result.
    Include the user's own words when they describe symptoms: a verdict of "urgent" means stop and tell them to
    seek emergency help. Use `wording` instead of ever calling a product safe. In Analyst mode, report the
    `compliance` checklist (pass / fail / review per legal requirement, each with its rule_id and citation), the
    mismatches and the decision in `next_step`: ready_for_sign_off (a named person still signs), request_evidence
    (list `evidence_needed`) or escalate. "needs_manual_review" means the reading was not reliable and no check
    ran. The rules screen a label; they never certify it.

    Args:
        label_text: The label text as printed (ingredient list plus allergen, gluten,
            lactose and diet statements, seals as "[seal: ...]"), or a recipe's ingredient list.
            Mark every word you are not sure of with [?].
        avoid: Restrictions, any of: lactose, milk, gluten, egg, soy, peanut, tree_nuts,
            sesame, fish, crustacean, mollusc, celery, mustard, sulphites, lupin, vegan, vegetarian.
            Empty list = analyst cross-check only.
        strict: True for an allergy or celiac disease (every unclear item becomes red).
        market: Label market: BR, US or EU.
        source: "photo", "text" (typed or pasted) or "recipe".
        transcription_confidence: "high" (every word clearly read), "medium" (some words unsure, marked [?])
            or "low" (parts blurred, cut off or hidden: no checks will run). Be honest; a wrong "high" defeats
            the safety gate.
        complete_pack: For photos, false when the photos may not show every panel of the pack.
    """
    result = engine.check_label(label_text, avoid, strict, market, matcher=_matcher, source=source,
                                transcription_confidence=transcription_confidence, complete_pack=complete_pack)
    review.audit("check_label", {"avoid": avoid, "strict": strict, "market": market, "source": source,
                                 "transcription_confidence": transcription_confidence, "complete_pack": complete_pack,
                                 "label_chars": len(label_text)}, result)
    return result


@mcp.tool()
def record_review_decision(check_id: str, reviewer: str, decision: str, reason: str = "", ticket: str = "",
                           reason_category: str = "", evidence: str = "", second_reviewer: str = "",
                           escalation_needed: bool | None = None) -> dict:
    """Record a named person's decision on a checked label (human sign-off). Only call it when the user, acting as
    the reviewer, states the decision. Never decide on their behalf.

    Args:
        check_id: The check_id returned by check_label.
        reviewer: Name or ID of the person signing.
        decision: "approve", "reject" or "approve_with_override". Approving a label the tool did not mark
            ready_for_sign_off counts as an override.
        reason: Required for a rejection or an override.
        ticket: Optional review ticket link.
        reason_category: Required for an override: supplier_evidence, transcription_error, data_error,
            rule_exception or artwork_pending. Ask the reviewer; never choose it for them.
        evidence: Required for an override on a critical finding (allergen, gluten or lactose statement, claim
            contradiction): the document, lab report or ticket that settles it.
        second_reviewer: Required for an override on a critical finding: a second person, not the reviewer.
        escalation_needed: Optional, when the tool escalated: the reviewer's view of whether it had to.
    """
    return review.record_decision(check_id, reviewer, decision, reason, ticket, reason_category, evidence,
                                  second_reviewer, escalation_needed)


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
def search_knowledge(query: str, k: int = 3) -> dict:
    """Find the passages of the project's knowledge files (label rules, glossaries, plain words, standards) that
    answer a question, each with an id to cite.

    Use it for questions the rules engine does not answer (what a term means, which evidence settles a claim, what a
    market requires) and whenever the knowledge files are not in your context. Answer only from the passages
    returned and cite their ids; if none is returned, say the knowledge files do not cover it. A passage marked
    to_verify is not confirmed against the official text: say so.
    """
    hits = knowledge.search(query, k=max(1, min(k, 5)))
    review.audit("search_knowledge", {"query": query}, {"coverage": f"{len(hits)} passages"})
    return {"passages": hits, "found": bool(hits),
            "note": "" if hits else "Not covered by the knowledge files. Do not answer from memory; say so."}


@mcp.tool()
def log_answer_without_check(reason: str, mode: str = "") -> dict:
    """Log that you answered about a label or an ingredient without calling check_label (monitoring, F-07).

    Call it when you judge a label or an ingredient (a verdict, a fit for a diet or an allergy) without check_label
    or lookup_ingredient, for example a label you could not send to the tool or a follow-up answered from an earlier
    result. Answers that rest on search_knowledge need no log.

    Args:
        reason: "general_question", "follow_up", "tool_unavailable" or "other".
        mode: "analyst", "shopper" or "cook".
    """
    review.audit("log_answer_without_check", {"reason": reason, "mode": mode}, {"mode": mode})
    return {"logged": True}


@mcp.tool()
def usage_stats() -> dict:
    """Usage and quality metrics from the audit log: checks, verdict mix, escalation reasons and rate, decisions and
    overrides, answers given without check_label."""
    return review.usage_stats()


if __name__ == "__main__":
    mcp.run()
