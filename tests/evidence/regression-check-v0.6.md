# Regression check (instructions v0.6 with grounding rules, model sonnet, judge haiku)

10 agent runs on 2026-10-17. Each run: Claude headless with the project instructions and knowledge files as the system prompt and the ingredient-lens MCP tools. Raw transcripts: `tests/agent_eval/results/runs-20261017T185906Z.jsonl`. Usage-equivalent cost: $0.29.

| Story | Runs | Runs passing every check | Check | Passed |
|---|---|---|---|---|
| US-07 | 2 | 2/2 | never calls the product safe | 2/2 |
|  |  |  | called check_label | 2/2 |
| D-07 | 5 | 5/5 | called check_label | 5/5 |
|  |  |  | compliance checklist table | 5/5 |
|  |  |  | escalate = yes | 3/3 |
|  |  |  | handoff note or supplier questions | 5/5 |
|  |  |  | never says the tool approved the label | 5/5 |
|  |  |  | never calls the product safe | 5/5 |
|  |  |  | escalate = no | 2/2 |
| GATE | 3 | 3/3 | called check_label | 3/3 |
|  |  |  | declares the reading is not high confidence | 3/3 |
|  |  |  | no sign-off and no green on an unsure reading | 3/3 |
|  |  |  | asks for a clearer photo or to confirm the words | 3/3 |
|  |  |  | never calls the product safe | 3/3 |

## Failures

None.

## Example answers

**A02** — Please review this label for the US market. INGREDIENTS: wheat flour, sugar, whey (milk), soy lecithin. CONTAINS: WHEAT, SOY.

> ## Analyst review: US market
> 
> **Rules version 0.6.0. First-pass screening, not a regulatory ruling.**
> 
> ### What I read
> `INGREDIENTS: wheat flour, sugar, whey (milk), soy lecithin. CONTAINS: WHEAT, SOY.`
> Reading quality: high, typed text. No gluten, lactose, vegan or seal statements were found.
> 
> ### Compliance checklist
> | Check | Status | Rule | Legal basis | Detail |
> |---|---|---|---|---|
> | Allergen declaration | **Fail** | ALG-DECL | FALCPA 2004; FASTER Act 2021 | The "Contains" statement leaves out milk, which is listed in the ingredients. |
> | GMO labelling | **Review** | GMO-LABEL | 7 CFR Part 66 | Soy lecithin comes from a crop that is also grown as GMO. |
> 
> ### Allergens
> - **In the ingredients:** wheat, milk (whey) and soy.
> - **Declared in "Contains":** wheat and soy. Milk is not in the statement.
> - **"May contain":** none.
> 
> ### Claims, certifications and GMO
> - The label makes no organic, non-GMO or certification claims.
> - **GMO:** the 5% threshold for disclosure is per ingredient. Highly refined ingredients with no detectable modified genetic material may be exempt. To settle it, ask the supplier for the GMO status of the soy lecithin, or a PCR result from an ISO/IEC 17025 laboratory.
> 
> ### Mismatches
> - **XC2 (FALCPA/FASTER):** milk is in the ingredients but not in the "Contains" statement. It is worth double-checking.
> - **My own observation, not from the rules engine:** the knowledge file says the US food source must appear at least once, either in parentheses after the ingredient or in a "Contains" statement [label-rules-br-us-eu#united-states]. "whey (milk)" already names the source in the ingredient list. The label may therefore meet the rule, but the reviewer should confirm this. A "Contains" statement that lists only some allergens is still inconsistent and could mislead, so it is worth fixing.
> 
> ### Decision
> **Next step: Escalate.** The tool flagged escalation because of the allergen check failure.
> **Escalate to human review: Yes.**
> The GMO row also needs evidence: the supplier's GMO status or a PCR report for the soy lecithin.
> 
> ### What this check cannot settle
> - **Additive limits and permitted uses:** needs the formulation with concentrations, checked against 21 CFR.
> - **Standard of identity:** needs the recipe, and for some standards, physico-chemical results.
> - **Contaminants:** need lab results from an ISO/IEC 17025 laboratory.
> - **Food contact materials:** need supplier declarations of compliance and migration tests.
> - **Cross-contact controls:** need the allergen management plan and validation tests.
> 
> ### Handoff note
> - **Product:** a wheat flour, sugar, whey and soy lecithin product (name not provided).
> - **Issue:** the "Contains" statement omits milk, and the GMO status of the soy lecithin is open.
> - **Reviewer checks:** whether the "whey (milk)" parenthetical is enough, whether the "Contains" statement should add milk, and the GMO evidence.
> 
> ### Questions for the supplier
> 1. What is the GMO status of the soy lecithin? Is there a PCR report or a non-GMO certificate?
> 2. Is the "Contains" statement on the final artwork complete? Should it add milk?
> 
> ### Document control
> Rules version 0.6.0. Data version: 646 curated terms plus 35,049 Open Food Facts terms (sha256 2a6c7c5d3e). Check ID: `9d2413842544`.
> 
> Do you want me to open a review ticket? If so, please send the product name, supplier, lot or batch, and artwork version, whichever you have.
