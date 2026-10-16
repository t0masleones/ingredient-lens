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


def audit(tool: str, inputs: dict, result: dict) -> None:
    summary = {k: result.get(k) for k in ("verdict", "escalate_to_human_review", "coverage", "mode", "ticket")}
    _append(AUDIT, {"at": _now(), "tool": tool, "inputs": inputs,
                    "result": {k: v for k, v in summary.items() if v is not None},
                    "mismatch_rules": [m["rule"] for m in result.get("mismatches", [])]})


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
    return {
        "checks": len(checks),
        "verdicts": dict(Counter(r["result"].get("verdict") for r in checks)),
        "escalation_rate": round(sum(bool(r["result"].get("escalate_to_human_review")) for r in checks)
                                 / max(len(checks), 1), 2),
        "mismatch_rules": dict(Counter(rule for r in checks for rule in r.get("mismatch_rules", []))),
        "tickets": sum(r["tool"] == "create_review_ticket" for r in rows),
        "first_call": rows[0]["at"], "last_call": rows[-1]["at"],
    }
