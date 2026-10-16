# Benchmark review (v0.4): what the engine missed, and what was fixed

Companion to `benchmark-rules-v0.4.md` (generated). This file is the manual review of every miss, done on 2026-10-16.

## Final result
- 6,000 real products (2,000 BR, 2,000 US, 1,000 FR, 1,000 DE), 160,570 engine runs, median 3.1 ms per label.
- 4,607 declared allergens checked: 4,090 🔴, 492 🟡, **25 🟢 (0.5%)**, same in STRICT mode.
- Coverage of ingredients found in the database: BR 93.1%, US 94.6%, FR 95.0%, DE 91.5%.
- Metamorphic properties: 94,097 checks. Deterministic, case-insensitive, STRICT never milder, "may contain milk" never improves a milk verdict: 0 failures. Ingredient order: 45 failures (0.2%), see below.

## The 25 remaining misses, one by one
| Cause | Count | Products |
|---|---|---|
| The allergen does not appear in the ingredient text (Open Food Facts took it from traces, a separate allergen box or a data error) | 22 | Organic Garbanzo Beans (gluten, milk), Organic Popcorn (milk), Light Rye Crispbread (milk), Tortilla Wraps (gluten; the text is a different product), Great Grains (milk; the text says "CONTAINS WHEAT AND PECANS"), Omega-3 Trail Mix (egg), Cacao céréales, Les Fourrées, Tartines Multi-Céréales, Saveir, Biscuits Petit déj (milk), Chicorée soluble (gluten), Reiswaffeln (sesame), Cornichons (egg, milk), Fette croccanti (milk), Pan Bauletto (egg, milk), Rummo Rigatoni (milk), kimchi 4056489152903 (fish, crustacean) |
| Ingredient text is unreadable OCR | 1 | Biscoito Aveia e Mel (soy) |
| The reference disagrees with the regulation or the label | 2 | Natural Coconut Cream (tree nuts: the FDA removed coconut in 2025 and EU Annex II does not list it), Paçoquita (gluten: the label says GLUTEN FREE and lists only peanut, sugar, salt) |
| **Engine error with the allergen readable in the text** | **0** | |

What this means: on this sample, the engine did not miss an allergen that was written in the ingredient text. It cannot see allergens that are only in a separate box or in the traces field, which is why the agent must transcribe every statement on the pack (instructions, section 2).

## Engine errors the benchmark found, now fixed and kept as tests
Each one is a test in `mcp-server/tests/test_benchmark_findings.py` or `test_review_findings.py`.

| Error | Example from the sample | Effect before the fix |
|---|---|---|
| A period inside parentheses, or used as a separator, ended the list | "MILK CHOCOLATE (SUGAR, MILK. CHOCOLATE, … LECITHIN (SOY)"; "HASELNÜSSE (13%). MAGERMILCHPULVER" | Soy and milk after the period were dropped: false greens |
| French trace wording not read as "may contain" | "Peut aussi contenir du lait", "Traces éventuelles de lait" | Possible milk not reported |
| Unnamed oil not flagged as possible soy | "Atum, água, óleo, sal" | 🟢 for soy where the oil is usually soybean |
| Claims before the list emptied it | "Sem glúten, Rico em fibras, Farinha de trigo…", "CONTÉM FENILALANINA Água…" | No ingredients read ("insufficient") |
| German ß changed in upper case | "WEISSWEIN" vs "Weißwein" | Verdict depended on letter case |
| Decimal commas split items | "chocolat noir 12,5%" | Items "chocolat noir 12" and "5%" |
| Open Food Facts allergen markup | "_Weizenmehl_" | Term not found |
| Oats treated as gluten in every market | 111 of 626 US "gluten-free" products came out 🔴, most with oats or "gluten free oats" | US false alarms; oats are not a gluten grain under 21 CFR 101.91 (now 🟡 in the US, 🔴 in BR and EU and in STRICT mode). Conflicts: 111 → 24 |
| "corn semolina" and "gluten free oats" inherited gluten from a word in the name | "Enriched corn meal" | False gluten alarms on corn |
| Missing basic terms | "sel", "eau", "blé", "riz", additive class names, vitamins | Unknown items (🟡 by default) |

A lesson worth keeping: adding coverage can raise false greens. When "blé" became a known term, some French labels that had been 🟡 only because of an unknown word turned 🟢, which exposed the missing trace wording. Coverage changes must always be re-measured on the benchmark.

## Still open
- **Ingredient order (45 cases, 0.2%).** Rejoining the parsed items in reverse order can move a statement keyword or a claim inside the list and change where it ends. These are mostly labels with claims or nutrition text mixed into the ingredient field. To review case by case (roadmap F-05).
- **Claims on the pack in conflict with the engine** (section 2 of the report): 24 of 626 US and 25 of 382 Brazilian "gluten-free" products, and many "lactose-free" products (BR 29 of 100, US 36 of 64, DE 26 of 66), mostly because milk is listed and lactase is not (XC3 asks for a person in that case). Each needs a person: it can be an engine false alarm, a data error or a real labeling issue (roadmap F-05).
