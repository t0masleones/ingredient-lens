# Analyst recheck (instructions v0.6 with F-07 and F-25, model sonnet, judge haiku)

5 agent runs on 2026-10-17. Each run: Claude headless with the project instructions and knowledge files as the system prompt and the ingredient-lens MCP tools. Raw transcripts: `tests/agent_eval/results/runs-20261017T183853Z.jsonl`. Usage-equivalent cost: $0.58.

| Story | Runs | Runs passing every check | Check | Passed |
|---|---|---|---|---|
| D-07 | 5 | 5/5 | called check_label | 5/5 |
|  |  |  | compliance checklist table | 5/5 |
|  |  |  | escalate = yes | 3/3 |
|  |  |  | handoff note or supplier questions | 5/5 |
|  |  |  | never says the tool approved the label | 5/5 |
|  |  |  | never calls the product safe | 5/5 |
|  |  |  | escalate = no | 2/2 |

## Failures

None.

## Example answers

**A02** — Please review this label for the US market. INGREDIENTS: wheat flour, sugar, whey (milk), soy lecithin. CONTAINS: WHEAT, SOY.

> **Market:** US. Rules version 0.6.0. First-pass screening, not a regulatory ruling.
> 
> ## What I read
> INGREDIENTS: wheat flour, sugar, whey (milk), soy lecithin. CONTAINS: WHEAT, SOY.
> - Gluten statement: not found. Lactose statement: not found. Vegan or vegetarian claim: none. Seals: none.
> - I read every word clearly, so ingestion passed.
> 
> ## Compliance checklist
> | Check | Status | Rule | Legal basis | Detail |
> |---|---|---|---|---|
> | Allergen declaration | **Fail** | ALG-DECL | FALCPA 2004; FASTER Act 2021 | The tool found milk in the ingredients but not in the CONTAINS statement. |
> | GMO labelling | **Review** | GMO-LABEL | 7 CFR Part 66 | Soy lecithin comes from a crop that is also grown as GMO. |
> 
> ## Allergens
> - **Found in the ingredients:** wheat, milk (whey), soy (soy lecithin).
> - **Declared in CONTAINS:** wheat, soy.
> - **May contain:** not declared. This is voluntary in the US.
> 
> ## Claims, certifications and GMO
> - The label makes no organic, non-GMO or other certification claim.
> - GMO: soy is a listed bioengineered crop and is presumed bioengineered unless records show otherwise. Disclosure is needed above 5% per ingredient. Highly refined ingredients with no detectable modified genetic material may be exempt.
> - To settle it, get the supplier's GMO status for the lecithin or a PCR result from an ISO/IEC 17025 laboratory.
> 
> ## Mismatches
> - **XC2:** milk is in the ingredients (whey) but not in the CONTAINS statement.
> - **My own observation, not from the rules engine:** the US rule only requires the allergen source to appear once. That can be in parentheses after the ingredient, as in "whey (milk)", or in a CONTAINS statement. As printed, milk is already declared in the ingredient list. The tool's fail may therefore be stricter than the rule, and the reviewer should decide.
> - Even so, a CONTAINS statement that leaves out milk while listing the other allergens is inconsistent. Many reviewers would want it added.
> 
> ## Decision
> **Escalate.** Escalate to human review: **Yes.**
> 
> ## What this check cannot settle
> - Additive limits and permitted uses: needs the formulation with concentrations.
> - Standard of identity: needs the recipe.
> - Contaminants: needs ISO/IEC 17025 lab results.
> - Food contact materials: needs supplier declarations of compliance and migration tests.
> - Cross-contact controls in the factory: needs the allergen management plan and validation tests.
> 
> ## Handoff note
> - **Product:** unnamed, US market, wheat flour, sugar, whey and soy lecithin.
> - **Issue:** the CONTAINS statement omits milk, although "whey (milk)" is in the ingredients. The soy lecithin GMO status is also open.
> - **Reviewer must check:** whether the parenthetical "(milk)" is enough or "MILK" should be added to CONTAINS, and the GMO evidence for the lecithin.
> 
> ## Questions for the supplier
> 1. Can you confirm the GMO status of the soy lecithin, or provide a PCR report?
> 2. Is there a shared line or other cross-contact risk that would justify a "may contain" statement?
> 
> ## Document control
> Rules version 0.6.0. Data version: 646 curated and 35049 Open Food Facts terms (sha256 2a6c7c5d3e). Check ID: `9d2413842544`.
> 
> I can open a review ticket if you want one. Please send the product name, supplier, lot or batch and artwork version.
