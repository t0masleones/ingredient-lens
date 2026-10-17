"""Judge saved plain-language (US-02) answers again, several times, to separate a real change from judge noise.

Usage (from mcp-server, CLAUDE_BIN set as for run_agent_eval.py):
    uv run python ../tests/agent_eval/rejudge_plain.py runs-A.jsonl runs-B.jsonl [--times 3]

Every saved US-02 answer in each file is judged --times times in one session with the same prompt and model. The
summary compares the files and reports how far the judge disagrees with itself on the same answer. Output:
tests/agent_eval/results/us02-rejudge-<A>-<B>.json. Costs a few cents (small judge model).
"""

from __future__ import annotations

import argparse
import json
import re
import statistics as st
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import run_agent_eval as ev


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="runs-*.jsonl files in results/")
    ap.add_argument("--times", type=int, default=3)
    args = ap.parse_args()
    cases = {c["id"]: c for c in (json.loads(l) for l in ev.CASES.open(encoding="utf-8") if l.strip())}
    jobs = []
    for f in args.files:
        for r in (json.loads(l) for l in (ev.RESULTS / Path(f).name).open(encoding="utf-8") if l.strip()):
            if r["story"] == "US-02":
                jobs += [(f, r["id"], r["repeat"], k + 1, r["text"]) for k in range(args.times)]

    def one(job):
        f, cid, rep, k, text = job
        _, detail = ev.judge_plain(cases[cid], text)
        m = re.match(r"(\d)/5", detail)
        return {"file": f, "id": cid, "repeat": rep, "judge_run": k, "score": int(m.group(1)) if m else None,
                "detail": detail}

    with ThreadPoolExecutor(6) as ex:
        out = list(ex.map(one, jobs))
    summary = {}
    for f in args.files:
        per_answer: dict[tuple, list[int]] = {}
        for o in out:
            if o["file"] == f and o["score"] is not None:
                per_answer.setdefault((o["id"], o["repeat"]), []).append(o["score"])
        scores = [s for v in per_answer.values() for s in v]
        summary[f] = {"judgements": len(scores), "mean": round(st.mean(scores), 2),
                      "share_4plus": round(sum(s >= 4 for s in scores) / len(scores), 3),
                      "answers": len(per_answer),
                      "answers_mean_4plus": sum(st.mean(v) >= 4 for v in per_answer.values()),
                      "same_answer_spread_mean": round(st.mean(max(v) - min(v) for v in per_answer.values()), 2)}
    stems = "-".join(Path(f).stem.removeprefix("runs-") for f in args.files)
    path = ev.RESULTS / f"us02-rejudge-{stems}.json"
    path.write_text(json.dumps({"judge_model": ev.JUDGE_MODEL, "times": args.times, "summary": summary,
                                "judgements": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
