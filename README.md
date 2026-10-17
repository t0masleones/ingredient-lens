<div align="center">

<img src="docs/assets/readme-banner.svg" alt="Ingredient Lens: label compliance, first pass. Rules engine, governed data and measured evidence for allergens, GMO and organic claims in Brazil, the US and the EU." width="100%">

<br>

<a href="https://github.com/t0masleones/ingredient-lens/actions/workflows/tests.yml"><img alt="CI status" src="https://github.com/t0masleones/ingredient-lens/actions/workflows/tests.yml/badge.svg"></a>
<img alt="Instructions v0.6" src="https://img.shields.io/badge/instructions-v0.6-00596B?style=flat-square">
<img alt="Rules engine 0.6.0" src="https://img.shields.io/badge/rules_engine-0.6.0-27787F?style=flat-square">
<img alt="3,274 tests passing" src="https://img.shields.io/badge/tests-3%2C274_passing-007681?style=flat-square">
<img alt="Benchmark on 6,000 real products" src="https://img.shields.io/badge/benchmark-6%2C000_real_products-1D4F91?style=flat-square">
<img alt="120 agent runs, 0 safe claims" src="https://img.shields.io/badge/agent_eval-120_runs%2C_0_%E2%80%9Csafe%E2%80%9D-00596B?style=flat-square&labelColor=27787F">
<img alt="Markets Brazil, US, EU" src="https://img.shields.io/badge/markets-BR_%C2%B7_US_%C2%B7_EU-FFE600?style=flat-square&labelColor=00596B">

<h3>
<a href="#-at-a-glance">At a glance</a> ·
<a href="#-how-it-works">How it works</a> ·
<a href="#-measured-evidence">Evidence</a> ·
<a href="#-quick-start">Quick start</a> ·
<a href="#-documentation">Documentation</a>
</h3>

</div>

**Ingredient Lens** is an AI agent for the **first-pass label compliance check** a regulatory or quality analyst does. It reads a label (photo or text), checks it against its own statements and the rules of its market, returns a checklist with the legal basis of each check, and ends every label in one of three decisions: **ready for sign-off** by a named reviewer, **request evidence** or **escalate**. The tool never approves a label. It also helps shoppers and cooks check labels against intolerances, allergies and animal or plant origin.

> [!IMPORTANT]
> **The model reads and explains. A tested rules engine decides. A person signs.** Claude transcribes the label and talks to the user; an MCP server applies the market rules, the ingredient data and the cross-checks, so the same label always gets the same verdict; a named reviewer records the decision, with a reason for any override.

**Scope.** In: what the label text shows (ingredients, allergen, gluten and lactose statements, claims and seals), checked against its own statements and the rules of Brazil, the US and the EU, as a first pass for a person to sign. Out: certifying anything, deciding the origin of an ambiguous ingredient without a supplier declaration, and anything not printed on the pack. For those, the agent says which evidence would settle the point.

<br>

## ✦ At a glance

<img src="docs/assets/readme-metrics.svg" alt="3,274 automated tests · 6,000 real products benchmarked · 0.5% of declared allergens missed · 0 “safe” claims in 120 agent runs" width="100%">

| Mode | Who | What they get |
|:--|:--|:--|
| 🧾 **Analyst** · *primary* | Regulatory or quality analyst | A compliance checklist per market (pass · fail · review, with the legal basis), GMO and certification claims, mismatches, a decision and a handoff note with supplier questions. [Analyst workflow →](docs/05-analyst-workflow.md) |
| 🛒 **Shopper** | Person with an intolerance or allergy | A short traffic-light verdict in plain words, with what to check next |
| 🍳 **Cook** | Cook serving guests with restrictions | A table with the origin and fit of each ingredient, and what to ask the supplier |

<br>

## ✦ How it works

```mermaid
%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#D5FAFE", "primaryTextColor": "#00596B", "primaryBorderColor": "#27787F", "lineColor": "#27787F", "secondaryColor": "#FFF7B3", "tertiaryColor": "#F1F6F6", "fontFamily": "Segoe UI, Arial, sans-serif"}}}%%
flowchart LR
  L[Label photo or text] --> S{Symptoms<br>described?}
  S -->|yes| EM[Emergency guidance only]
  S -->|no| T[Claude transcribes<br>every statement]
  T --> G{Reading<br>reliable?}
  G -->|no| MR[No verdict:<br>ask for a clearer photo]
  G -->|yes| R[check_label<br>rules engine]
  D[(653 curated +<br>35,043 public terms)] --- R
  RR[(Rule register<br>basis · dates · tests)] --- R
  R --> C[Market checklist<br>BR · US · EU]
  C -->|all pass| A[Ready for sign-off]
  C -->|evidence missing| E[Request evidence]
  C -->|fail or contradiction| X[Escalate]
  A --> SO[Named reviewer signs]
  X --> K[Review ticket<br>with traceability]
```

<details>
<summary><b>The five MCP tools</b></summary>
<br>

| Tool | What it returns | Why it is not left to the model |
|:--|:--|:--|
| `check_label` | Verdict per restriction, findings, cross-checks XC1–XC5, the market `compliance` checklist with a `rule_id` and legal basis per row, `next_step` (ready_for_sign_off · request_evidence · escalate), `evidence_needed`, the `ingestion` gate, the `wording` to use instead of “safe”, and a `check_id` with the rules and data versions | Same input, same answer, tested in code |
| `lookup_ingredient` | One term from the SQLite database, with its source | Governed, versioned data instead of free text |
| `create_review_ticket` | A GitHub Issue or a local queue entry with product, supplier, lot, artwork version and failed checks | Human in the loop, with traceability |
| `record_review_decision` | The reviewer's signed decision on a `check_id` (approve, reject, approve with override); an override needs a reason and its category, and on a critical finding also evidence and a second approver | The tool never approves; overrides are justified and audited |
| `usage_stats` | Verdict mix, escalation rate, decisions, override rate and uncertainty rate from the audit log | Monitoring after go-live, including automation bias |

</details>

### Principles built into the agent

> [!CAUTION]
> **Emergency first.** If someone describes symptoms happening now, the agent gives emergency guidance only (SAMU 192, 911, 112) and does not analyse the label. The rules engine enforces this too.

> [!WARNING]
> **Never “safe”.** A product is never called safe, organic, non-GMO, certified or compliant. The agent says what the label claims and which evidence settles it: a certificate from a body accredited to ISO/IEC 17065, a lab report from an ISO/IEC 17025 laboratory, or a supplier record.

> [!WARNING]
> **Fails closed.** If the agent cannot read the label reliably, no check runs and it asks for a clearer photo of the whole pack. If a word is unsure, nothing can pass. A misread word that looks clean is the most dangerous error, so it is never allowed to become a pass.

> [!NOTE]
> **Every rule names its basis.** The [rule register](docs/07-rule-register.md) holds each rule's legal basis per market (RDC 26/2015 and Lei 10.674/2003, FALCPA and 21 CFR 101.91, Regulation 1169/2011, plus GMO and organic rules), the date it applies from, how well it was checked, its history and its tests. A basis not yet verified returns “review”, never “pass”, and CI fails when a rule's review is overdue.

<br>

## ✦ Measured evidence

| What was measured | Result | Report |
|:--|:--|:--|
| Rules engine on 6,000 real products | 22 of 4,607 declared allergens missed (0.5%): 20 not in the ingredient text, 2 where the reference and the rule disagree, 0 engine errors; coverage 91.7–95.1%; 94,153 property checks | [benchmark](tests/evidence/benchmark-rules-v0.6.md) · [review](tests/evidence/benchmark-review-v0.6.md) |
| Second reference: the manufacturer's own statement | 98.7% of declared allergens flagged from the ingredients alone, with the statement removed; 91.3% of definite flags confirmed by the statement | [benchmark §5](tests/evidence/benchmark-rules-v0.6.md) |
| Text extraction, by input type | Ingredient list read in 99.9% of 6,000 product texts; recipes only in the golden set; **photos not measured yet** | [benchmark §1](tests/evidence/benchmark-rules-v0.6.md) |
| Full agent: never “safe” | 0 claims in 120 runs, 36 of them adversarial | [agent evaluation v0.6](tests/evidence/agent-eval-v0.6.md) |
| Full agent: emergency first | 21/21, and no false emergency on a past reaction (3/3) | [agent evaluation v0.6](tests/evidence/agent-eval-v0.6.md) |
| Full agent: Analyst and certification decisions | 15/15 Analyst cases (never says the tool approved), 12/12 GMO and certification cases | [agent evaluation v0.6](tests/evidence/agent-eval-v0.6.md) |
| Full agent: unsure readings and sign-off | 9/9 unsure readings declared and stopped; 6/6 overrides recorded only with a reason | [agent evaluation v0.6](tests/evidence/agent-eval-v0.6.md) |
| Full agent: plain language | Objective checks 18/18; model judge 4+/5 in 8/18 runs, unchanged from v0.5 in a controlled re-judge. **Partly met** | [agent evaluation v0.6](tests/evidence/agent-eval-v0.6.md) |
| Golden set (text rows) | 25/25, written by the author, so not an unbiased figure | [results](tests/evidence/results-rules-v0.6.md) |
| Curated data without a source | 68 of 83 rows sourced by an automated cross-check; 15 left for a person | [cross-check](tests/evidence/curated-crosscheck.md) |

> [!TIP]
> The benchmark has found thirteen real engine errors so far, each fixed and kept as a regression test. Four came in v0.6, once every number had to explain itself. One example: a statement printed inside an ingredient's parentheses, such as “arôme naturel (contient alcool)”, ended the ingredient list, so gelatin listed after it came out 🟢 for a vegan.

<br>

## ✦ Quick start

<details>
<summary><b>1 · Use it as a Claude Project</b> (no code, about 10 minutes)</summary>
<br>

1. In Claude, open **Projects → New project** and name it “Ingredient Lens”.
2. Paste [`agent/project-instructions.md`](agent/project-instructions.md) into the project's instructions.
3. Add the files in [`agent/knowledge/`](agent/knowledge/) to the project's files.
4. Open a chat, attach a photo of an ingredient panel or paste the text, and say what you need to avoid, or write “analyst mode” and the market.

</details>

<details>
<summary><b>2 · Connect the rules engine to Claude Desktop</b> (MCP, needs <a href="https://docs.astral.sh/uv/">uv</a>)</summary>
<br>

In Claude Desktop: **Settings → Developer → Edit Config**, add the block below with your path, then restart the app. In Claude Code, the [`.mcp.json`](.mcp.json) at the repository root connects it automatically; it calls `uv` by name, so restart the editor after installing uv to pick up the new PATH.

```json
{
  "mcpServers": {
    "ingredient-lens": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\path\\to\\ingredient-lens\\mcp-server", "server.py"],
      "env": { "INGREDIENT_LENS_GITHUB_REPO": "your-user/ingredient-lens" }
    }
  }
}
```

Leave out `env` to keep review tickets in a local file. If Claude Desktop does not find `uv`, use its full path in `command`.

</details>

<details>
<summary><b>3 · Run the tests and evaluations</b></summary>
<br>

```bash
cd mcp-server
uv run pytest                                      # 3,274 unit, data and property tests
uv run eval_rules.py                               # golden set, text rows
uv run python ../tests/benchmark/run_benchmark.py  # 6,000 real products, about 45 minutes
# full agent evaluation (uses your Claude login): set CLAUDE_BIN to the Claude Code executable
uv run python ../tests/agent_eval/run_agent_eval.py --repeats 3
```

</details>

<details>
<summary><b>4 · Build the documentation site</b></summary>
<br>

```bash
uv run --no-project --with markdown==3.7 python docs/_build/build.py
```

Open `docs/index.html` in a browser. To publish it, enable GitHub Pages with **Settings → Pages → Deploy from a branch → main → /docs**.

</details>

<br>

## ✦ Documentation

The documentation is a static site in [`docs/`](docs/) (open `docs/index.html`), generated from the Markdown files below, which also read well here on GitHub.

| | Document | What it covers |
|:--|:--|:--|
| 📒 | [Project record](docs/00-project-record.md) | Activity log, decision log, traceability, quality metrics, risks and the prioritised backlog |
| 🔎 | [Discovery](docs/01-discovery.md) | Problem, personas, current processes, business relevance |
| ⚖️ | [Tool and data selection](docs/02-tool-selection.md) | Build vs buy for the agent and for its data |
| ✅ | [Requirements](docs/03-requirements.md) | User stories with measurable acceptance criteria |
| 🧭 | [Critical review and roadmap](docs/04-critical-review.md) | What the evidence does and does not show, and what comes next |
| 🧾 | [Analyst workflow](docs/05-analyst-workflow.md) | To-be process, roles, checks per market, decision rule, ROI model, pilot plan |
| 🏅 | [Standards alignment](docs/06-standards-alignment.md) | Certification (ISO/IEC 17065), testing (ISO/IEC 17025), GMO and organic rules, and how the agent follows them |
| 📜 | [Rule register](docs/07-rule-register.md) | Every rule with its legal basis per market, dates, verification level, history and tests, and how rule changes are released |
| 🧪 | [Test plan](tests/test-plan.md) | Every test layer, from unit tests to the agent evaluation |
| 📝 | [Changelog](agent/CHANGELOG.md) | What changed in each version |

<details>
<summary><b>Repository map</b></summary>
<br>

| Path | What it is |
|:--|:--|
| [`agent/`](agent/) | Instructions, knowledge files (label rules, glossaries, plain words, standards and certifications) and the changelog |
| [`mcp-server/`](mcp-server/) | The MCP server: rules engine, [rule register](mcp-server/rules/register.json), ingredient data ([sources, licenses and governance](mcp-server/data/README.md)), review queue, audit log, tests |
| [`tests/`](tests/) | Test plan, golden set, benchmark sample of real products, agent evaluation cases and transcripts, evidence reports |
| [`docs/`](docs/) | Documentation sources (Markdown) and the generated site (`_build/build.py`, `assets/`) |
| [`.github/`](.github/) | Continuous integration (tests and golden set on every push, benchmark on demand) and issue forms for rule changes and disputed ingredient mappings |

</details>

<br>

## ✦ Limitations

> [!WARNING]
> - **Photos are not measured yet.** Transcription can fail on curved packs, glare and tiny print. The agent declares how well it read the label and the engine fails closed on an unsure reading, but that declaration is the model's own judgement until a photo test set calibrates it.
> - **A label cannot show everything.** Processing aids, cross-contact and allergens printed outside the transcribed text are invisible to the rules.
> - **Plain language is partly met** in the default shopper format, and no user test (UAT) has been done yet.
> - **Some legal bases are not verified yet**, and dates are recorded but not applied: the [rule register](docs/07-rule-register.md) marks each one, and checks on an unverified basis return “review”.
> - For an allergy or celiac disease, always confirm with the manufacturer and a health professional.

<br>

<div align="center">
<sub>
Independent prototype by <a href="https://github.com/t0masleones">t0masleones</a>. Not affiliated with any company. Not medical, legal or regulatory advice.<br>
Ingredient data includes Open Food Facts terms, © Open Food Facts contributors, available under the <a href="https://opendatacommons.org/licenses/odbl/1-0/">Open Database License</a>.
</sub>
</div>
