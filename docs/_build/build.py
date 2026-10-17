"""Build the documentation site in docs/ from the Markdown sources and the project record fragment.

Usage (from the repository root):
    uv run --no-project --with markdown==3.7 python docs/_build/build.py

Sources stay the single source of truth:
- docs/*.md, tests/test-plan.md, tests/evidence/*.md, agent/CHANGELOG.md  (Markdown, also readable on GitHub)
- docs/src/00-project-record.html                                          (HTML fragment with record components)
Output: static pages in docs/ that open from disk (file://) and can be served by GitHub Pages (main, /docs).
Numbers on the home page are read from tests/benchmark/results.json, the latest agent evaluation report and the
data files, so they cannot drift from the evidence.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import subprocess
from pathlib import Path

import markdown

DOCS = Path(__file__).resolve().parent.parent
ROOT = DOCS.parent
REPO = "https://github.com/t0masleones/ingredient-lens"
BLOB = REPO + "/blob/main/"
TREE = REPO + "/tree/main/"
TESTS_PASSED = "3,145"          # update after each full pytest run (unit, data and property tests)
SITE = "Ingredient Lens"


def latest_agent_eval() -> str:
    reports = sorted((ROOT / "tests" / "evidence").glob("agent-eval-v*.md"),
                     key=lambda p: [int(x) for x in re.findall(r"\d+", p.stem)])
    return reports[-1].relative_to(ROOT).as_posix()


PAGES = [
    {"out": "index.html", "kind": "home", "nav": "Home", "group": "Overview", "title": SITE,
     "desc": "A first-pass label compliance agent for Brazil, the US and the EU: rules engine, governed data and "
             "measured evidence."},
    {"out": "00-project-record.html", "kind": "html", "src": "docs/src/00-project-record.html", "base": "docs",
     "nav": "Project record", "group": "Overview", "title": "Project record", "eyebrow": "Living document",
     "desc": "The running record of the project from the Business Analyst's side: activity, decisions, "
             "traceability, quality, risks and backlog."},
    {"out": "01-discovery.html", "src": "docs/01-discovery.md", "nav": "Discovery", "group": "Analysis",
     "title": "Discovery", "eyebrow": "01 · Discovery",
     "desc": "The problem, the people who have it, how they work today and why it matters to a food business."},
    {"out": "02-tool-selection.html", "src": "docs/02-tool-selection.md", "nav": "Tool and data selection",
     "group": "Analysis", "title": "Tool and data selection", "eyebrow": "02 · Build vs buy",
     "desc": "No-code versus custom for the agent, and curated versus public data for its knowledge, with sources "
             "checked and dated."},
    {"out": "03-requirements.html", "src": "docs/03-requirements.md", "nav": "Requirements", "group": "Analysis",
     "title": "Requirements", "eyebrow": "03 · Requirements",
     "desc": "User stories with measurable acceptance criteria, non-functional requirements and the definition of "
             "done."},
    {"out": "05-analyst-workflow.html", "src": "docs/05-analyst-workflow.md", "nav": "Analyst workflow",
     "group": "Delivery", "title": "Analyst workflow", "eyebrow": "05 · Primary use case",
     "desc": "Label compliance first pass: to-be process, roles, checks per market, the decision rule and an ROI "
             "model ready for a pilot."},
    {"out": "06-standards-alignment.html", "src": "docs/06-standards-alignment.md", "nav": "Standards alignment",
     "group": "Delivery", "title": "Standards alignment", "eyebrow": "06 · Certification, testing, compliance",
     "desc": "How the agent maps to the standards behind certification and testing work, and the guidelines it now "
             "follows."},
    {"out": "04-critical-review.html", "src": "docs/04-critical-review.md", "nav": "Critical review and roadmap",
     "group": "Delivery", "title": "Critical review and roadmap", "eyebrow": "04 · Honest assessment",
     "desc": "What the evidence shows and does not show, the weaknesses found, and the prioritised roadmap."},
    {"out": "test-plan.html", "src": "tests/test-plan.md", "nav": "Test plan", "group": "Evidence",
     "title": "Test plan", "eyebrow": "Evidence · Method",
     "desc": "How the agent and the rules are tested, from unit tests to benchmarks on real products and the agent "
             "evaluation."},
    {"out": "benchmark-review.html", "src": "tests/evidence/benchmark-review-v0.4.md", "nav": "Benchmark review",
     "group": "Evidence", "title": "Benchmark on 6,000 real products", "eyebrow": "Evidence · Rules engine",
     "desc": "The manual review of every miss on real products from four markets, and the engine errors it found."},
    {"out": "agent-evaluation.html", "src": latest_agent_eval(), "nav": "Agent evaluation", "group": "Evidence",
     "title": "Agent evaluation", "eyebrow": "Evidence · Claude with the tools",
     "desc": "Repeated runs of the full agent: safety, emergency guidance, plain language, Analyst decisions and "
             "certification claims."},
    {"out": "data-crosscheck.html", "src": "tests/evidence/curated-crosscheck.md", "nav": "Data cross-check",
     "group": "Evidence", "title": "Data cross-check", "eyebrow": "Evidence · Data governance",
     "desc": "Curated rows without a source, checked against a public dataset, and the decisions taken."},
    {"out": "changelog.html", "src": "agent/CHANGELOG.md", "nav": "Changelog", "group": "Reference",
     "title": "Changelog", "eyebrow": "Reference",
     "desc": "What changed in each version of the agent, the rules and the data."},
]
GROUPS = ["Overview", "Analysis", "Delivery", "Evidence", "Reference"]
HEADER_NAV = [("Home", "index.html"), ("Project record", "00-project-record.html"),
              ("Analyst workflow", "05-analyst-workflow.html"), ("Standards", "06-standards-alignment.html"),
              ("Evidence", "test-plan.html")]
OUT_BY_SRC = {p["src"]: p["out"] for p in PAGES if p.get("src")}
OUT_BY_SRC["docs/00-project-record.html"] = "00-project-record.html"

ICONS = {
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    "github": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .5a11.5 11.5 0 0 0-3.64 22.42c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.33-1.28-1.69-1.28-1.69-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.71 1.26 3.37.96.1-.75.4-1.26.73-1.55-2.56-.29-5.25-1.28-5.25-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.42-2.7 5.4-5.27 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5Z"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    "moon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 11.5l2.5 2.5L16 9"/><path d="M12 3l7 3v5c0 4.6-3 8.3-7 10-4-1.7-7-5.4-7-10V6z"/></svg>',
    "alert": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M12 8v5M12 17h.01"/><path d="M10.3 3.9 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>',
    "data": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></svg>',
    "doc": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></svg>',
}

TITLES = {"note": "Note", "tip": "Tip", "important": "Important", "warning": "Warning", "caution": "Caution"}
HERO_ARCS = ('<svg class="hero-arcs" viewBox="0 0 560 420" aria-hidden="true" focusable="false">'
             '<circle cx="430" cy="120" r="150" fill="none" stroke="#27787F" stroke-width="26"/>'
             '<circle cx="520" cy="360" r="120" fill="none" stroke="#FFFFFF" stroke-opacity=".9" stroke-width="18"/>'
             '<circle cx="250" cy="330" r="34" fill="none" stroke="#FFE600" stroke-width="9"/></svg>')


# ------------------------------------------------------------------ helpers

def git_date(rel: str) -> str:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT, capture_output=True,
                             text=True, timeout=20).stdout.strip()
        return out or dt.date.today().isoformat()
    except (OSError, subprocess.SubprocessError):
        return dt.date.today().isoformat()


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def convert_alerts(md_text: str) -> str:
    lines, out, i = md_text.split("\n"), [], 0
    while i < len(lines):
        m = re.match(r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$", lines[i])
        if m:
            kind, buf, i = m.group(1).lower(), [], i + 1
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append(f'<div class="callout {kind}" markdown="1">\n<span class="callout-title">{TITLES[kind]}</span>\n\n'
                       + "\n".join(buf) + "\n\n</div>")
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def rewrite_links(fragment: str, base_dir: Path) -> str:
    def fix(m: re.Match) -> str:
        href = html.unescape(m.group(1))
        if href.startswith(("http://", "https://", "mailto:", "#", "data:")):
            return m.group(0)
        path, _, frag = href.partition("#")
        if not path:
            return m.group(0)
        target = (base_dir / path).resolve()
        try:
            key = target.relative_to(ROOT).as_posix()
        except ValueError:
            return m.group(0)
        if key in OUT_BY_SRC:
            new = OUT_BY_SRC[key]
        elif key.startswith("docs/") and not key.endswith(".md") and target.exists():
            new = key[len("docs/"):]
        else:
            new = (TREE if target.is_dir() else BLOB) + key
        return f'href="{html.escape(new + ("#" + frag if frag else ""), quote=True)}"'
    return re.sub(r'href="([^"]+)"', fix, fragment)


def add_anchors(fragment: str) -> str:
    def fix(m: re.Match) -> str:
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        idm = re.search(r'id="([^"]+)"', attrs)
        if not idm or 'class="anchor"' in inner:
            return m.group(0)
        return (f'<{tag}{attrs}>{inner}<a class="anchor" href="#{idm.group(1)}" '
                f'aria-label="Link to this section">#</a></{tag}>')
    return re.sub(r"<(h[23])([^>]*)>(.*?)</\1>", fix, fragment, flags=re.S)


def wrap_diagrams(fragment: str) -> str:
    return re.sub(r'(<pre class="mermaid">.*?</pre>)', r'<figure class="diagram">\1</figure>', fragment, flags=re.S)


def toc_from_html(fragment: str) -> list[dict]:
    toc = []
    for m in re.finditer(r'<(h[23])[^>]*id="([^"]+)"[^>]*>(.*?)</\1>', fragment, flags=re.S):
        name = html.escape(text_of(re.sub(r'<a class="anchor".*?</a>', "", m.group(3))))
        item = {"id": m.group(2), "name": name, "children": []}
        if m.group(1) == "h2" or not toc:
            toc.append(item)
        else:
            toc[-1]["children"].append(item)
    return toc


def toc_html(toc: list[dict], cls: str = "") -> str:
    if not toc:
        return ""
    parts = []
    for t in toc:
        kids = "".join(f'<li><a href="#{c["id"]}">{c["name"]}</a></li>' for c in t["children"])
        parts.append(f'<li><a href="#{t["id"]}">{t["name"]}</a>' + (f"<ol>{kids}</ol>" if kids else "") + "</li>")
    return f'<ol{(" class=" + chr(34) + cls + chr(34)) if cls else ""}>' + "".join(parts) + "</ol>"


def sections_for_search(page: dict, body: str) -> list[dict]:
    entries = [{"p": page["nav"], "s": page["title"], "u": page["out"], "x": page["desc"]}]
    chunks = re.split(r'(?=<h[23][^>]*id=")', body)
    for chunk in chunks:
        m = re.match(r'<h[23][^>]*id="([^"]+)"[^>]*>(.*?)</h[23]>', chunk, flags=re.S)
        if not m:
            continue
        title = text_of(re.sub(r'<a class="anchor".*?</a>', "", m.group(2)))
        entries.append({"p": page["nav"], "s": title, "u": f'{page["out"]}#{m.group(1)}',
                        "x": text_of(chunk[m.end():])[:420]})
    return entries


# ------------------------------------------------------------------ page bodies

def render_markdown(page: dict) -> tuple[str, list[dict]]:
    src = ROOT / page["src"]
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"\A#\s+.*\n", "", text, count=1)               # the title moves to the hero
    blocks: list[str] = []

    def stash(m: re.Match) -> str:
        blocks.append(m.group(1))
        return f"\n\nMERMAIDBLOCK{len(blocks) - 1}\n\n"
    text = re.sub(r"^```mermaid[ \t]*\n(.*?)\n```[ \t]*$", stash, text, flags=re.M | re.S)
    text = convert_alerts(text)
    md = markdown.Markdown(extensions=["extra", "toc", "sane_lists"],
                           extension_configs={"toc": {"toc_depth": "2-3"}})
    body = md.convert(text)
    for i, code in enumerate(blocks):
        body = body.replace(f"<p>MERMAIDBLOCK{i}</p>",
                            f'<figure class="diagram"><pre class="mermaid">{html.escape(code)}</pre></figure>')
    body = re.sub(r"<table>", '<div class="table-wrap"><table>', body)
    body = body.replace("</table>", "</table></div>")
    body = rewrite_links(body, src.parent)
    body = add_anchors(body)
    return body, toc_from_html(body)


def render_fragment(page: dict) -> tuple[str, list[dict]]:
    body = (ROOT / page["src"]).read_text(encoding="utf-8")
    body = re.sub(r"\A<!--.*?-->\s*", "", body, flags=re.S)
    body = rewrite_links(body, ROOT / page.get("base", "docs"))
    body = wrap_diagrams(add_anchors(body))
    return body, toc_from_html(body)


def facts() -> dict:
    bench = json.loads((ROOT / "tests" / "benchmark" / "results.json").read_text(encoding="utf-8"))
    cov = [v * 100 for v in bench["coverage"].values()]
    report = (ROOT / latest_agent_eval()).read_text(encoding="utf-8")
    runs = int(re.search(r"(\d+) agent runs", report).group(1))
    safe = [tuple(map(int, m)) for m in re.findall(r"never calls the product safe \| (\d+)/(\d+)", report)]
    emergency = re.search(r"tells to seek emergency help \| (\d+)/(\d+)", report)
    curated = sum(1 for _ in open(ROOT / "mcp-server" / "data" / "ingredients.csv", encoding="utf-8")) - 1
    imported = sum(1 for _ in open(ROOT / "mcp-server" / "data" / "off-terms.csv", encoding="utf-8")) - 1
    return {
        "products": f'{bench["products"]:,}', "allergens": f'{bench["allergen_checks"]:,}',
        "missed": bench["false_greens"], "missed_rate": f'{bench["false_green_rate"] * 100:.1f}%',
        "coverage": f"{min(cov):.1f}–{max(cov):.1f}%", "runs": runs,
        "unsafe": sum(t - ok for ok, t in safe), "safe_total": sum(t for _, t in safe),
        "emergency": f"{emergency.group(1)}/{emergency.group(2)}" if emergency else "n/a",
        "curated": f"{curated:,}", "imported": f"{imported:,}", "tests": TESTS_PASSED,
    }


def readme_metrics_svg(f: dict) -> str:
    """Metric cards for the README, drawn from the same facts as the home page so they never drift."""
    cards = [
        (f["tests"], "automated tests", "unit, data and property, every push"),
        (f["products"], "real products benchmarked", "most scanned in BR, US, FR and DE"),
        (f["missed_rate"], "declared allergens missed", f'{f["missed"]} of {f["allergens"]}; none readable in text'),
        (str(f["unsafe"]), f'“safe” claims in {f["runs"]} agent runs', f'emergency guidance first: {f["emergency"]}'),
    ]
    w, h, gap, pad = 1280, 210, 18, 22
    cw = (w - 2 * pad - 3 * gap) / 4
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
             f'aria-label="{html.escape(" · ".join(f"{n} {t}" for n, t, _ in cards), quote=True)}">',
             '<defs><clipPath id="c"><rect width="1280" height="210" rx="22"/></clipPath></defs>',
             '<g clip-path="url(#c)"><rect width="1280" height="210" fill="#F2FEFF"/>',
             '<circle cx="1262" cy="-20" r="70" fill="none" stroke="#D5FAFE" stroke-width="16"/></g>']
    for i, (num, label, sub) in enumerate(cards):
        x = pad + i * (cw + gap)
        parts.append(
            f'<g transform="translate({x:.1f},{pad})"><rect width="{cw:.1f}" height="{h - 2 * pad}" rx="16" fill="#FFFFFF" '
            f'stroke="#D5E6E8"/><rect x="0" y="22" width="5" height="44" rx="2.5" fill="#FFE600"/>'
            f'<text x="24" y="66" font-family="Fraunces, Georgia, \'Times New Roman\', serif" font-size="46" '
            f'font-weight="700" fill="#00596B">{html.escape(num)}</text>'
            f'<text x="24" y="106" font-family="Signika, \'Segoe UI\', Arial, sans-serif" font-size="18" '
            f'font-weight="600" fill="#12282D">{html.escape(label)}</text>'
            f'<text x="24" y="134" font-family="Signika, \'Segoe UI\', Arial, sans-serif" font-size="14.5" '
            f'fill="#5B6B6E">{html.escape(sub)}</text></g>')
    parts.append("</svg>\n")
    return "".join(parts)


def home_body(f: dict) -> str:
    cards = []
    icon_for = {"Overview": "doc", "Analysis": "doc", "Delivery": "check", "Evidence": "data", "Reference": "doc"}
    for p in PAGES[1:]:
        cards.append(f'<a class="card" href="{p["out"]}"><span class="icon">{ICONS[icon_for[p["group"]]]}</span>'
                     f'<p class="eyebrow">{html.escape(p["group"])}</p><h3>{html.escape(p["title"])}</h3>'
                     f'<p>{html.escape(p["desc"])}</p><span class="more">Read →</span></a>')
    flow = """flowchart TD
  L[Label photo or text] --> S{Symptoms described?}
  S -->|yes| EM[Emergency guidance only]
  S -->|no| T[Agent transcribes every statement]
  T --> R[check_label rules engine]
  D[(Curated + public ingredient data)] --- R
  R --> C[Market checklist BR, US, EU]
  C -->|all pass| A[Approve]
  C -->|evidence missing| E[Request evidence]
  C -->|fail or contradiction| X[Escalate with handoff note]
  X --> K[Review ticket with traceability]"""
    return f"""
<section class="home-hero">
  <div class="container">
    <div>
      <p class="eyebrow">AI agent · Business analysis case study</p>
      <h1>Label compliance, first pass. Measured like a regulated product.</h1>
      <p class="lead">Ingredient Lens reads a food label, checks it against its own statements and the rules of
      Brazil, the US and the EU, and hands anything doubtful to a person. The model reads and explains; a tested
      rules engine decides.</p>
      <div class="hero-actions">
        <a class="btn btn-accent" href="00-project-record.html">Read the project record</a>
        <a class="btn btn-ghost-light" href="05-analyst-workflow.html">See the analyst workflow</a>
      </div>
    </div>
    <div class="hero-visual" aria-hidden="true">
      <div class="hero-shape"></div><div class="hero-ring"></div>
      <div class="check-card">
        <h2>Compliance checklist</h2>
        <p class="sub">Market: BR · rules 0.4.0 · data {f["curated"]} + {f["imported"]} terms</p>
        <ul>
          <li>Allergen declaration <span class="pill pass">Pass</span></li>
          <li>Gluten statement <span class="pill pass">Pass</span></li>
          <li>GMO labelling <span class="pill review">Review</span></li>
          <li>Organic claim <span class="pill review">Review</span></li>
          <li>“Contém lactose” statement <span class="pill fail">Fail</span></li>
        </ul>
        <p class="decision">Decision: escalate · handoff note ready</p>
      </div>
    </div>
  </div>
</section>
<p class="strip"><span>Rules engine</span><span>Governed data</span><span>Measured evidence</span></p>

<section class="section">
  <div class="container">
    <div class="section-head"><p class="eyebrow">Evidence, not promises</p>
      <h2>What has been measured</h2>
      <p>Every number below comes from a versioned test run in the repository.</p></div>
    <div class="metrics">
      <div class="metric"><b>{f["tests"]}</b><span>automated tests on every push</span><small>Unit, data and property tests in continuous integration.</small></div>
      <div class="metric"><b>{f["products"]}</b><span>real products benchmarked</span><small>Most scanned in Brazil, the US, France and Germany. Coverage {f["coverage"]}.</small></div>
      <div class="metric"><b>{f["missed_rate"]}</b><span>declared allergens missed</span><small>{f["missed"]} of {f["allergens"]}; none was readable in the ingredient text.</small></div>
      <div class="metric"><b>{f["unsafe"]}</b><span>“safe” claims in {f["runs"]} agent runs</span><small>Including adversarial prompts. Emergency guidance first: {f["emergency"]}.</small></div>
    </div>
  </div>
</section>

<section class="section soft">
  <div class="container">
    <div class="section-head"><p class="eyebrow">What it does</p><h2>Built around the analyst, safe for everyone</h2></div>
    <div class="cards">
      <div class="card"><span class="icon">{ICONS["check"]}</span><h3>Analyst first pass</h3><p>A checklist per market with the legal basis of each check, then one of three decisions: approve, request evidence or escalate with a handoff note.</p></div>
      <div class="card"><span class="icon">{ICONS["alert"]}</span><h3>Safety in code</h3><p>Symptoms described now get emergency guidance only. A product is never called “safe”. Allergy and celiac profiles turn every doubt red.</p></div>
      <div class="card"><span class="icon">{ICONS["data"]}</span><h3>Governed data and evidence</h3><p>Every ingredient row cites its source. Screening is never presented as certification or as a lab result; each claim names the evidence that settles it.</p></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head"><p class="eyebrow">How it works</p><h2>The model reads and explains. The tools decide.</h2></div>
    <figure class="diagram"><pre class="mermaid">{html.escape(flow)}</pre></figure>
  </div>
</section>

<section class="section soft">
  <div class="container">
    <div class="section-head"><p class="eyebrow">Documentation</p><h2>Everything behind the agent</h2>
      <p>Discovery, decisions, requirements, the analyst workflow, standards and the evidence, kept as living documents.</p></div>
    <div class="cards">{"".join(cards)}</div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="cta-band">
      <h2>Start with the project record</h2>
      <p>The activity log, decision log, traceability from story to test, quality metrics, risks and the prioritised backlog, on one page.</p>
      <div class="hero-actions">
        <a class="btn btn-accent" href="00-project-record.html">Open the project record</a>
        <a class="btn btn-ghost-light" href="{REPO}">View the repository</a>
      </div>
    </div>
  </div>
</section>"""


# ------------------------------------------------------------------ layout

def sidebar(current: str) -> str:
    groups = []
    for g in GROUPS:
        items = "".join(
            f'<li><a href="{p["out"]}"{" aria-current=" + chr(34) + "page" + chr(34) if p["out"] == current else ""}>'
            f'{html.escape(p["nav"])}</a></li>' for p in PAGES if p["group"] == g)
        groups.append(f'<div class="sidebar-group"><p class="sidebar-title">{g}</p><ul>{items}</ul></div>')
    return (f'<aside class="sidebar" id="sidebar" aria-label="Documentation">{"".join(groups)}'
            '<p class="sidebar-note">Independent prototype. Screening aid, not medical, legal or regulatory advice.</p>'
            '</aside><div class="drawer-backdrop" aria-hidden="true"></div>')


def page_html(page: dict, body: str, toc: list[dict], prev_p: dict | None, next_p: dict | None) -> str:
    is_home = page["kind"] == "home"
    nav = "".join(f'<a href="{href}"{" aria-current=" + chr(34) + "page" + chr(34) if href == page["out"] else ""}>{label}</a>'
                  for label, href in HEADER_NAV)
    title = page["title"] if is_home else f'{page["title"]} · {SITE}'
    mermaid = ('<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js" defer></script>'
               if 'class="mermaid"' in body else "")
    if is_home:
        main = f'<main id="content" tabindex="-1">{body}</main>{sidebar(page["out"])}'
    else:
        src = page["src"]
        words = len(text_of(body).split())
        hero = f"""
<section class="page-hero">
  {HERO_ARCS}
  <div class="container">
    <nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="index.html">Docs</a></li><li>{page["group"]}</li><li aria-current="page">{html.escape(page["nav"])}</li></ol></nav>
    <p class="eyebrow">{html.escape(page.get("eyebrow", page["group"]))}</p>
    <h1>{html.escape(page["title"])}</h1>
    <p class="lead">{html.escape(page["desc"])}</p>
    <ul class="meta"><li>Updated {git_date(src)}</li><li>{max(1, round(words / 220))} min read</li><li>Source: {html.escape(Path(src).name)}</li></ul>
  </div>
</section>"""
        pager = '<nav class="pager" aria-label="Previous and next">'
        if prev_p:
            pager += f'<a class="prev" href="{prev_p["out"]}"><small>Previous</small><span>{html.escape(prev_p["title"])}</span></a>'
        if next_p:
            pager += f'<a class="next" href="{next_p["out"]}"><small>Next</small><span>{html.escape(next_p["title"])}</span></a>'
        pager += "</nav>"
        toc_block = (f'<nav class="toc" aria-label="On this page"><p class="toc-title">On this page</p>{toc_html(toc)}</nav>'
                     if toc else '<div></div>')
        inline = (f'<div class="toc-inline"><details><summary>On this page</summary>{toc_html(toc)}</details></div>'
                  if toc else "")
        main = f"""{hero}
<div class="layout container">
  {sidebar(page["out"])}
  <main id="content" class="content" tabindex="-1">
    {inline}
    <article class="prose">{body}</article>
    {pager}
    <p class="page-meta"><a href="{BLOB}{src}">View source on GitHub</a><a href="{REPO}/edit/main/{src}">Suggest an edit</a><span>Generated by docs/_build/build.py</span></p>
  </main>
  {toc_block}
</div>"""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(page["desc"], quote=True)}">
<meta name="theme-color" content="#00596B">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(page["desc"], quote=True)}">
<link rel="icon" href="assets/icon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Open+Sans:wght@400;600;700&family=Signika:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="assets/site.css">
<script>(function(){{try{{var t=localStorage.getItem("il-theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}}})();</script>
</head>
<body class="page-{"home" if is_home else "doc"}" data-base="">
<a class="skip-link" href="#content">Skip to content</a>
<div class="progress" aria-hidden="true"><span></span></div>
<div class="utility-bar"><div class="container">
  <p>Independent prototype · not affiliated with any company · not medical, legal or regulatory advice</p>
  <nav aria-label="Utility"><a href="changelog.html">Changelog</a><a href="{REPO}">GitHub</a>
    <button class="theme-toggle" type="button" data-theme-toggle aria-pressed="false">{ICONS["moon"]}<span data-theme-label>Dark mode</span></button></nav>
</div></div>
<header class="site-header"><div class="container">
  <button class="btn btn-outline menu-button" type="button" aria-controls="sidebar" aria-expanded="false" aria-label="Open navigation">{ICONS["menu"]}</button>
  <a class="brand" href="index.html"><img class="brand-mark" src="assets/icon.svg" alt="" width="38" height="38"><span class="brand-name">{SITE}<small>Documentation</small></span></a>
  <nav class="main-nav" aria-label="Main">{nav}</nav>
  <div class="header-actions">
    <button class="btn btn-outline" type="button" data-search-open aria-label="Search the documentation">{ICONS["search"]}<span class="label">Search</span><kbd>Ctrl K</kbd></button>
    <a class="btn btn-accent" href="{REPO}">{ICONS["github"]}<span class="label">Repository</span></a>
  </div>
</div></header>
{main}
<footer class="site-footer"><div class="container">
  <div><a class="brand" href="index.html"><img class="brand-mark" src="assets/icon.svg" alt="" width="38" height="38"><span class="brand-name">{SITE}</span></a>
    <p>A first-pass label compliance agent built and documented as a business analysis case study.</p></div>
  <div><h2>Documentation</h2><ul><li><a href="00-project-record.html">Project record</a></li><li><a href="05-analyst-workflow.html">Analyst workflow</a></li><li><a href="06-standards-alignment.html">Standards alignment</a></li><li><a href="04-critical-review.html">Critical review</a></li></ul></div>
  <div><h2>Evidence</h2><ul><li><a href="test-plan.html">Test plan</a></li><li><a href="benchmark-review.html">Benchmark review</a></li><li><a href="agent-evaluation.html">Agent evaluation</a></li><li><a href="data-crosscheck.html">Data cross-check</a></li></ul></div>
  <div><h2>Project</h2><ul><li><a href="{REPO}">Repository</a></li><li><a href="changelog.html">Changelog</a></li><li><a href="{BLOB}mcp-server/data/README.md">Data sources and licenses</a></li></ul></div>
  <p class="footer-bottom">Independent prototype by t0masleones. Not affiliated with any company. Not medical, legal or regulatory advice. Ingredient data includes Open Food Facts terms, © Open Food Facts contributors, ODbL 1.0.</p>
</div></footer>
<div class="search" role="dialog" aria-modal="true" aria-label="Search the documentation" hidden>
  <div class="search-panel">
    <label class="search-field">{ICONS["search"]}<span class="visually-hidden">Search</span>
      <input type="search" placeholder="Search the documentation" autocomplete="off" spellcheck="false" role="combobox" aria-expanded="true" aria-controls="search-results"></label>
    <ul class="search-results" id="search-results" role="listbox"></ul>
    <p class="search-foot"><span><kbd>↑</kbd> <kbd>↓</kbd> to move</span><span><kbd>Enter</kbd> to open</span><span><kbd>Esc</kbd> to close</span></p>
  </div>
</div>
<div class="toast" role="status" aria-live="polite"></div>
<script src="assets/search-index.js" defer></script>
{mermaid}
<script src="assets/site.js" defer></script>
</body>
</html>
"""


def main() -> None:
    f = facts()
    rendered, index = [], []
    for page in PAGES:
        kind = page.get("kind", "md")
        if kind == "home":
            body, toc = home_body(f), []
        elif kind == "html":
            body, toc = render_fragment(page)
        else:
            body, toc = render_markdown(page)
        page.setdefault("kind", kind)
        rendered.append((page, body, toc))
        index += sections_for_search(page, body)
    for i, (page, body, toc) in enumerate(rendered):
        prev_p = rendered[i - 1][0] if i > 0 else None
        next_p = rendered[i + 1][0] if i + 1 < len(rendered) else None
        (DOCS / page["out"]).write_text(page_html(page, body, toc, prev_p, next_p), encoding="utf-8", newline="\n")
    (DOCS / "assets" / "search-index.js").write_text(
        "window.__SEARCH__ = " + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8", newline="\n")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "assets" / "readme-metrics.svg").write_text(readme_metrics_svg(f), encoding="utf-8", newline="\n")
    print(f"{len(rendered)} pages, {len(index)} search entries. Facts: {f}")


if __name__ == "__main__":
    main()
