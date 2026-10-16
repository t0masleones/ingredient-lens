# 02 - Tool selection (no-code vs custom, build vs buy)

## Decision to make
Which approach gives a trustworthy ingredient-checking assistant fastest, at zero cost, with a clear path to engineering if the idea proves valuable?

## Requirements that drive the choice
- Zero cost to build and test; nothing public.
- Reads photos of labels.
- Follows strict behavior rules (never reassure, mark uncertainty, escalate).
- Reproducible by someone else from this repository.

## Options compared (checked 2026-10-16)
| Option | Free to build? | Photo input | Control and testing | Verdict |
|---|---|---|---|---|
| Claude Project (no-code) | Yes. Projects are available on the free plan, up to five | Yes, images attached in the chat | Instructions and knowledge files, versioned in this repo | **Chosen for the prototype** |
| ChatGPT custom GPT | No. Personal accounts, including free, can no longer create GPTs, and OpenAI is retiring them in favor of plugins | n/a | n/a | Rejected |
| Claude AI-powered artifact (small app) | Yes. Available on free plans; each viewer's usage counts against their own plan | To test | More code to maintain | Candidate for v0.2 |
| Custom app on an LLM API | Free API tiers exist but have tight daily limits | Yes | Full control, needs developers and hosting | Only if the pilot proves value |
| Buy an existing regulatory SaaS | No | n/a | Mature data and support | Out of scope; this prototype complements such tools |

## What the no-code agent cannot do (triggers for engineering)
- Connect to live company data or a governed ingredient database.
- Provide an audit trail, usage metrics or monitoring out of the box.
- Be shared by link on the free plan (sharing is a Team and Enterprise feature), and large-knowledge retrieval is a paid feature.
- Guarantee identical answers on every run.
- Handle customer data under company privacy rules: this prototype uses only public or invented examples.

## Recommendation
1. Build and test v0.1 as a Claude Project (this repo).
2. Use the golden set to measure accuracy, then iterate to v0.2.
3. If the pilot shows value, write the hand-off for engineering (below).

## Hand-off sketch for engineering
Example data mapping for a production version (replaces the knowledge files with governed data):

| Field | Description | Example | Future source |
|---|---|---|---|
| ingredient_raw | Text as printed or typed | mono- and diglycerides | Label or recipe |
| ingredient_id | Normalized ingredient | ING-0231 | Ingredient master data |
| origin_class | animal, plant, mineral/synthetic, microbial, either, unknown | either | Supplier specification |
| allergen_groups | Allergen groups present | none | Regulatory library |
| evidence | Where the classification comes from | Supplier declaration, doc 123 | Document store |
| confidence | high, medium, low | medium | Model plus rules |

Integration needs: connector or API to the ingredient and specification data, logging of every answer with its evidence, a human-review queue for 🟡 and 🔴 cases, and access control.

## Data sources for the ingredient database (v0.3, checked 2026-10-16)
The same build-vs-buy question applies to data: curate everything by hand, or reuse a public dataset.

| Source | Regulated? | Machine-readable? | What it adds | Decision |
|---|---|---|---|---|
| Open Food Facts taxonomies (additives, ingredients) | No, volunteer-maintained; follows the EU additive list | Yes, JSON, ODbL license | 10,902 terms in PT, EN and ES; vegan and vegetarian status; E/INS codes | **Imported** for diet status and coverage. Allergens are never assumed absent without evidence |
| Codex CXG 36-1989 (INS) | Yes, international standard | No, PDF | Additive numbers and functions | Used through the E/INS code mapping |
| Anvisa IN 211/2023 | Yes, Brazil | No, amended often | Additives authorized in Brazil | Cited in the label rules |
| EU additives database (Regulation 1333/2008, Annex II) | Yes, EU | Searchable only | Authorized E numbers | Cited; Open Food Facts follows it |
| FDA Substances Added to Food | Yes, US | Searchable only | About 4,000 substances | Backlog, if a download becomes available |
| USDA FoodData Central, TACO (Brazil) | Yes, public | Yes | Nutrient composition | Not used: out of scope (nutrition) |

Rule for any imported data: the curated rows win, the import is a script whose output is versioned and reviewed as a diff, and a gap in the data must produce 🟡, never 🟢. Details: [mcp-server/data/README.md](../mcp-server/data/README.md).

## Sources
- Open Food Facts taxonomies: https://static.openfoodfacts.org/data/taxonomies/ and terms of use (ODbL): https://world.openfoodfacts.org/terms-of-use
- EU food additives database: https://food.ec.europa.eu/food-safety/food-improvement-agents/additives/database_en
- FDA Substances Added to Food: https://www.fda.gov/food/food-additives-petitions/substances-added-food-formerly-eafus
- Codex INS working documents: https://www.fao.org/fileadmin/user_upload/codexalimentarius/invitations/CCFA55_INS2025.pdf
- Claude Projects on free plans, sharing and RAG limits: https://support.claude.com/en/articles/9517075
- Claude AI-powered artifacts: https://support.claude.com/en/articles/9487310
- Image upload guidance: https://support.claude.com/en/articles/8241126-upload-files-to-claude
- Free Claude usage limits: https://support.claude.com/en/articles/8602283-about-free-claude-usage
- OpenAI custom GPT retirement: https://help.openai.com/en/articles/20001519
- Personal accounts cannot create GPTs: https://www.jotform.com/ai/what-is-a-custom-gpt/
