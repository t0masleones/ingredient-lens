"""Human-review queue and audit log.

Every tool call is appended to logs/audit.jsonl. Review tickets go to GitHub Issues
when INGREDIENT_LENS_GITHUB_REPO is set (owner/name), otherwise to logs/review-queue.jsonl.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
AUDIT = LOG_DIR / "audit.jsonl"
QUEUE = LOG_DIR / "review-queue.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _append(path: Path, record: dict) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


AUDIT_KEYS = ("check_id", "input_sha256", "rules_version", "data_version", "verdict", "next_step",
              "escalate_to_human_review", "requires_sign_off", "coverage", "mode", "ticket", "decision", "reviewer")
DECISIONS = {"approve", "reject", "approve_with_override"}


def audit(tool: str, inputs: dict, result: dict) -> None:
    """One line per tool call. A check is identified by check_id (input hash + rules and data version), so a
    reviewer's decision can be traced to the exact input, rules and data that produced it."""
    summary = {k: result.get(k) for k in AUDIT_KEYS}
    record = {"at": _now(), "tool": tool, "inputs": inputs,
              "result": {k: v for k, v in summary.items() if v is not None},
              "mismatch_rules": [m["rule"] for m in result.get("mismatches", [])]}
    if "compliance" in result:
        record["compliance"] = {c["rule_id"] or c["check"]: c["status"] for c in result["compliance"]}
    if "ingestion" in result:
        record["ingestion_gate"] = result["ingestion"].get("gate")
    _append(AUDIT, record)


def find_check(check_id: str) -> dict | None:
    """The last check_label record with this check_id in the audit log."""
    if not AUDIT.exists():
        return None
    hit = None
    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("tool") == "check_label" and row.get("result", {}).get("check_id") == check_id:
                hit = row
    return hit


def record_decision(check_id: str, reviewer: str, decision: str, reason: str = "", ticket: str = "") -> dict:
    """A named person's decision on a checked label. Approving a label the tool did not mark ready for sign-off is
    an override and needs a reason; so does a rejection. Returns the record, or an error the agent must show."""
    decision = decision.strip().lower()
    if decision not in DECISIONS:
        return {"error": f"decision must be one of {sorted(DECISIONS)}"}
    if not reviewer.strip():
        return {"error": "a named reviewer is required"}
    check = find_check(check_id)
    if check is None:
        return {"error": f"no check_label run with check_id {check_id} in the audit log"}
    tool_step = check["result"].get("next_step")
    override = decision.startswith("approve") and tool_step != "ready_for_sign_off"
    if override and decision == "approve":
        decision = "approve_with_override"
    if (override or decision == "reject") and not reason.strip():
        return {"error": f"a reason is required: the tool's decision was '{tool_step}'"}
    record = {"check_id": check_id, "reviewer": reviewer.strip(), "decision": decision, "tool_next_step": tool_step,
              "override": override, "reason": reason.strip(), "ticket": ticket,
              "rules_version": check["result"].get("rules_version"), "data_version": check["result"].get("data_version")}
    audit("record_review_decision", {"check_id": check_id}, record)
    return {**record, "recorded_at": _now()}


def _github_token() -> str | None:
    if token := os.environ.get("GITHUB_TOKEN"):
        return token
    # Reuse the credential Git already has for github.com (Git Credential Manager), without prompting.
    try:
        out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                             capture_output=True, text=True, timeout=15,
                             env={**os.environ, "GCM_INTERACTIVE": "never", "GIT_TERMINAL_PROMPT": "0"})
    except (OSError, subprocess.TimeoutExpired):
        return None
    return next((line[9:] for line in out.stdout.splitlines() if line.startswith("password=")), None)


def create_ticket(title: str, body: str) -> dict:
    repo = os.environ.get("INGREDIENT_LENS_GITHUB_REPO")
    record = {"at": _now(), "title": title, "body": body, "ticket": f"local:{QUEUE.name}"}
    destination = "local queue"
    if repo and (token := _github_token()):
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues", method="POST",
            data=json.dumps({"title": title, "body": body}).encode(),
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        # If GitHub fails, the case still lands in the local queue instead of being lost.
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                record["ticket"] = json.load(resp)["html_url"]
            destination = "github"
        except (OSError, ValueError, KeyError) as e:
            record["github_error"] = str(e)
    elif repo:
        record["github_error"] = "no GitHub token found"
    _append(QUEUE, record)
    return {"ticket": record["ticket"], "destination": destination, **({"error": record["github_error"]}
                                                                        if "github_error" in record else {})}


def usage_stats() -> dict:
    rows = [json.loads(line) for line in AUDIT.read_text(encoding="utf-8").splitlines()
            if line.strip()] if AUDIT.exists() else []
    if not rows:
        return {"checks": 0}
    checks = [r for r in rows if r["tool"] == "check_label"]
    decisions = [r for r in rows if r["tool"] == "record_review_decision"]
    n = max(len(checks), 1)
    return {
        "checks": len(checks),
        "verdicts": dict(Counter(r["result"].get("verdict") for r in checks)),
        "next_steps": dict(Counter(r["result"].get("next_step") for r in checks)),
        "escalation_rate": round(sum(bool(r["result"].get("escalate_to_human_review")) for r in checks) / n, 2),
        "uncertainty_rate": round(sum(r.get("ingestion_gate") in ("blocked", "degraded") for r in checks) / n, 2),
        "mismatch_rules": dict(Counter(rule for r in checks for rule in r.get("mismatch_rules", []))),
        "tickets": sum(r["tool"] == "create_review_ticket" for r in rows),
        "decisions": dict(Counter(r["result"].get("decision") for r in decisions)),
        "override_rate": round(sum(r["result"].get("decision") == "approve_with_override" for r in decisions)
                               / max(len(decisions), 1), 2),
        "first_call": rows[0]["at"], "last_call": rows[-1]["at"],
    }
