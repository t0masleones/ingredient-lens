# Benchmark review (v0.6): what the numbers mean

Companion to [`benchmark-rules-v0.6.md`](benchmark-rules-v0.6.md) (generated: rules 0.6.0, data sha256 d9d2171dfc, 167,319 engine runs on 6,000 products). This file reads those numbers by hand, on 2026-10-17. It answers the external review's question about extraction (section 1), explains every miss (section 2), checks the engine against the manufacturers' own statements (section 3), separates real false alarms from gaps in the reference (section 4), and lists what the benchmark exposed: four engine errors, now fixed (section 5), and data that a second reviewer must decide (section 6).

> [!IMPORTANT]
> **In short.** No allergen written in the ingredient text was missed: the 22 misses (0.5% of 4,607) are 20 allergens that are not in the text at all and 2 where the reference disagrees with the rule. With the manufacturer's statement removed, the engine still flags 98.7% of what manufacturers declare. Most "false alarms" against the reference are gaps in the reference (93.5% name the allergen in the text). The benchmark found four engine errors, now fixed, and eight places where the data or a rule makes the engine too cautious; those wait for a second reviewer. Photos are not measured.

## 1. Extraction by input type
The external review asked: *what percentage of cases did the system confidently extract the ingredient list and the allergen and gluten statements, split by photo, text and recipe?*

| Input type | Cases | Ingredient list extracted | Allergen statement found | Gluten statement found (Brazil, where it is mandatory) | How confidence is handled |
|---|---|---|---|---|---|
| Text (product ingredient field) | 6,000 | 5,993 (99.9%) | 1,138 of 5,993 (19.0%) | 538 of 1,995 (27.0%) | Typed or pasted text is read as given (`transcription_confidence` "high"); a word marked [?] still blocks every pass |
| Recipe (typed list) | 10 golden cases (V01–V10) | 10 of 10 read and judged as expected | n/a | n/a | Same as text |
| Photo | 0 | **not measured** | **not measured** | **not measured** | The agent declares the confidence; the gate's behaviour is tested (unit tests and 9/9 agent runs), its calibration is not (F-02) |

| Market | Products | Ingredient list extracted | Allergen statement found | Gluten statement found | Any statement found |
|---|---|---|---|---|---|
| BR | 2,000 | 99.8% | 24.2% | 27.0% | 32.3% |
| US | 2,000 | 99.9% | 12.9% | 0.4% | 13.2% |
| FR | 1,000 | 100.0% | 23.5% | 0.6% | 23.8% |
| DE | 1,000 | 100.0% | 16.2% | 1.0% | 17.0% |

How to read the statement columns: Open Food Facts usually stores only the ingredient list, not the separate allergen and gluten lines of the pack, so "not found" here mostly describes the data source, not the engine. The engine's own reading of statements is checked where they are present (section 3), and the agent is told to transcribe every panel. Photos are the input that matters most in practice and the one not yet measured; until they are, the ingestion gate is the safeguard, and it relies on the confidence the model declares (risk R-12).

## 2. Misses against reference A, and why
Reference A is the allergens Open Food Facts records for each product. "Detected" means the engine flags the allergen for a profile avoiding it, 🔴 or 🟡.

| Result | Count | Share |
|---|---|---|
| 🔴 Definite flag | 4,093 | 88.8% |
| 🟡 Possible: a person checks | 492 | 10.7% |
| 🟢 Missed | 22 | 0.5% |

A 🟡 is the right answer when the text does not settle the question, but it is not the same as finding the allergen: 224 of the 492 include an item the database does not know and 307 an ingredient whose source is not stated (a product can have several reasons). Counting only 🔴, detection is 88.8%. In v0.4 the split was 4,090 🔴, 492 🟡 and 25 🟢.

Every miss was read by hand. The keyword lists that sort them are independent of the engine's database.

| Cause | Misses | Products (allergen, market) and what the text shows |
|---|---|---|
| The allergen is not in the ingredient text: the reference took it from traces, a separate allergen box or a data error | 20 | **US:** Great Grains cereal (milk), Light Rye Crispbread (milk), Organic Garbanzo Beans (gluten, milk), Organic Popcorn (milk), Tortilla Wraps (gluten; the text is a different product), Omega-3 Trail Mix (egg) · **FR:** Cacao céréales (milk), Chicorée soluble (gluten), Les Fourrées (milk), Tartines Craquantes (milk), Saveir Sel & Vinaigre (milk), Biscuits Petit déj (milk) · **DE:** Reiswaffeln (sesame), Fette croccanti (milk), Pan Bauletto Bianco (egg, milk), Rummo Mezzi Rigatoni (milk), kimchi 4056489152903 (crustacean, fish) |
| The reference disagrees with the rule or the label | 2 | **BR:** Paçoquita (gluten; the label says GLUTEN FREE and lists only peanut, sugar and salt) · **FR:** Natural Coconut Cream (tree_nuts; coconut is on neither the FDA list (since 2025) nor EU Annex II) |
| The text could not be read (ingestion) | 0 | — |
| **Engine error with the allergen readable in the text** | **0** | — |

**Compared with v0.4 (25 misses):** three fewer. Biscoito Aveia e Mel (soy) is now detected because of a real fix: the "DERIVADOS DE SOJA" statement split by a period. The other two are Cornichons Gurken (egg, milk): the parenthesis fix restored "Senf" and "Gewürzextrakt" as ingredients, and an imported term cannot rule an allergen out, so egg and milk are now 🟡. Those allergens are still not in the text, so that change is caution, not detection.

What this means: on this sample, no allergen that is written in the ingredient text was missed. The engine cannot see an allergen printed only in a separate box, in the traces field of the database, or on another panel, which is why the agent transcribes every statement on the pack.

## 3. Reference B: the manufacturers' own statements
For the products whose text includes an allergen statement, the ingredients were checked again **without the statement**, so the engine could not find an allergen by reading the declaration.

| Market | Products with a statement | Allergens declared | Flagged from the ingredients alone | 🔴 flags the statement also declares | Labels whose statement leaves a required allergen out (XC2) |
|---|---|---|---|---|---|
| BR | 457 | 880 | 870 (98.9%) | 660 of 716 (92.2%) | 26 (5.7%) |
| US | 172 | 289 | 284 (98.3%) | 249 of 272 (91.5%) | 18 (10.5%) |
| FR | 5 | 12 | 12 (100.0%) | 6 of 8 (75.0%) | 1 (20.0%) |
| DE | 10 | 10 | 10 (100.0%) | 10 of 17 (58.8%) | 3 (30.0%) |
| **All** | **644** | **1,191** | **1,176 (98.7%)** | **925 of 1,013 (91.3%)** | **48 (7.5%)** |

Recall from the ingredients alone: 98.7%. The 15 declared allergens not flagged, read by hand: 7 are texts that are not an ingredient list (a nutrition table, marketing copy, a brewery address, OCR that turns NÃO CONTÉM GLÚTEN into CONTÉM), 5 are declarations with no source in the list (a precautionary CONTÉM GLÚTEN on potato straws and tomato paste, a soup base not listed), 1 is a typo in the source (ovas for ovos), and 2 are an engine rule: a facility line read as part of a Contains statement (section 6). Precision: 91.3% of the definite flags are also declared; the rest are what XC2 sends to a person. In Brazil (26 labels), soy lecithin, peanut and milk powder listed without a declaration look like real omissions or statements cut short in the data, while nutmeg read as a tree nut (5 labels) is a data error (section 6). Many US cases are French labels in the US sample, judged by US rules. Before the parenthesis fix, France and Germany had 37 and 45 labels with a statement; most were notes in parentheses.

## 4. False alarms: gaps in the reference, or the engine?
A 🔴 for an allergen that reference A does not record is not proof of a false alarm: the reference is incomplete. Each such flag was split by whether an independent keyword list sees the allergen in the text.

| Allergen | Products without it in reference A | 🔴 | Named in the text (reference incomplete) | Not named (upper bound on false alarms) |
|---|---|---|---|---|
| celery | 5,886 | 40 | 39 | 1 |
| crustacean | 5,986 | 5 | 2 | 3 |
| egg | 5,729 | 152 | 134 | 18 |
| fish | 5,921 | 52 | 37 | 15 |
| gluten | 4,732 | 712 | 693 | 19 |
| lupin | 5,986 | 8 | 8 | 0 |
| milk | 4,866 | 862 | 849 | 13 |
| mollusc | 5,986 | 39 | 35 | 4 |
| mustard | 5,915 | 44 | 44 | 0 |
| peanut | 5,780 | 125 | 121 | 4 |
| sesame | 5,918 | 91 | 91 | 0 |
| soy | 5,132 | 569 | 538 | 31 |
| sulphites | 5,920 | 102 | 55 | 47 |
| tree_nuts | 5,538 | 238 | 195 | 43 |
| **All** | **79,295** | **3,039** | **2,841 (93.5%)** | **198 (0.25% of pairs)** |

Of the 3,039 flags, 2,841 (93.5%) name the allergen in the text: the reference is incomplete, not the engine wrong. The other 198, 0.25% of all product–allergen pairs, are the upper bound on false alarms. The first 40 of them, read by hand, fall into four groups:

| What the flags without a keyword turned out to be (read by hand) | Examples | What to do |
|---|---|---|
| Correct: the allergen is there, in a word the keyword list lacks | "soybean", "lecitina de soia", "œufs", "requeijão", "queso", "Greek yoghurt", "avellanas", "almendras" | Nothing in the engine; extend the benchmark's keyword list |
| Correct by design: a cautious reading | "non-dairy" (in the US it may still contain caseinate, a milk protein), "lactic acid bacteria" (cultures can be grown on milk), "molho de soja" for gluten (soy sauce is usually brewed with wheat) | Keep; explain in the answer |
| Data candidates: a wrong fact, or a word that means something else in another language | Soy flour carries gluten; the Dutch "room" (cream) matches the English "room" ("store at controlled room temperature" read as milk); the French "râpé" (grated) loses its accent and matches the Spanish "rape" (monkfish), so "noix de coco râpé" reads as fish; "macarrão caracol" (a pasta shape) reads as snail; "mayonesa vegano" reads as egg; artificial hazelnut or almond flavour reads as the nut | Section 6: each one makes a term milder, so it needs a second reviewer |
| Noise in the source text | OCR text "DO SOLE CALOR" (for "do sol e calor") matched the fish "sole" | Nothing in the data; the ingestion gate exists for unreadable text |

## 5. Engine errors the benchmark found in v0.6, now fixed and kept as tests
Each one is a test in `mcp-server/tests/test_benchmark_findings.py`.

| Error | Example from the sample | Effect before the fix | How it surfaced |
|---|---|---|---|
| A statement split by a period was not read | "CONTÉM GLÚTEN. DERIVADOS DE SOJA" | The soy declaration was lost | Failure buckets: the only "parsing" miss |
| A statement inside an ingredient's parentheses ended the list | "arôme naturel (contient alcool)", "vinagre (contém sulfitos)", "coconut flakes 28% (contains: sulfur dioxide)" | Every ingredient after it was dropped (gelatin came out 🟢 for a vegan), and the rest of the list was read as the label's allergen statement: false XC2 mismatches, and a declaration the label does not have | Reference B: XC2 on 40% of French and 29% of German labels with a statement |
| "Contains one or more of the following" read as an allergen statement | "Vegetable Oil Contains One Or More Of The Following: Corn, Soybean, … Whey, Nonfat Dry Milk" | Same as above; milk reported as declared | Reference B, reading the "declared but not found" cases |
| An unclosed parenthesis in OCR text hid the rest of the label | "farinha de trigo (glutenamido de milho, … Pode conter vestígios de: crustáceos, ovo, peixe"; "ÓLEOS VEGETAIS (CONTEM OLEO DE SOJA, AGUA, … SORO DE LEITE" | The traces line became part of an ingredient, so traces were read as contents; in the second label the list was cut and the whey lost | The ingredient-order property: failures rose from 45 to 280 after the second fix, and the cause was this. The second label came up while reading reference B by hand |

A lesson for the next round: the second fix made the metamorphic property fail more, not less, and that is how the third error was found. A property test that gets worse after a fix is evidence, not noise.

## 6. Candidate data changes, waiting for a second reviewer
Each change below makes a term milder (fewer allergens), so under the data governance policy it needs a second reviewer and a regression test before it is applied ([disputed mappings](../../mcp-server/data/README.md#governance)). Until then the engine stays cautious: these cause false alarms, never false greens.

| Term | What the engine says now | Proposed | Evidence to check | Effect |
|---|---|---|---|---|
| Nutmeg in Portuguese and German ("noz-moscada", "Muskatnuss") | Tree nuts, definite (entry "nutmeg-nut"), while the English "nutmeg" has none | No tree nut, like the English entry | FDA tree-nut list (Edition 5 guidance) and EU Regulation 1169/2011 Annex II: nutmeg is a spice seed, on neither list | The largest single source of false XC2 escalations in Brazil (mortadela, lasagne, instant noodles, honey cake) |
| Soy flour (soy flour, farinha de soja, farine de soja, Sojamehl) | Contains gluten and soy (Open Food Facts entry, inherited) | Soy; gluten possible (🟡), not certain | Codex and FDA definitions of soy flour; the taxonomy's parent link | Fewer false gluten alarms and false XC1 and XC2 mismatches |
| "creme de milho" (creamed corn) | Milk, definite (matched "creme") | Milk possible (🟡) | Product composition; supplier specification | Fewer false milk flags on corn products |
| "room" | Milk (Dutch synonym of cream) | Keep for Dutch labels only, or drop as a common English word | The import's language rules (`import_off.py`) | Removes false milk flags on English storage text |
| "rape" | Fish (Spanish synonym of monkfish); the French "râpé" (grated) matches it once accents are removed | Match it only as a whole Spanish item, or keep accents for this word | The import's language rules | Removes false fish flags on French "râpé" (grated coconut, cheese, carrots) |
| "caracol" | Mollusc (snail) | Not when it names a pasta shape ("macarrão caracol", "caracolito") | Product context | Removes a false mollusc flag on pasta |
| "mayonesa vegana", "mayonesa vegano" | Egg (matched "mayonesa") | Curated rows without egg, like "maionese vegana" | Product category definition | Fewer false egg flags |
| Artificial hazelnut or almond flavour ("saborizante artificial a avellana", "esencia artificial de almendra") | Tree nuts, definite | Tree nuts possible (🟡) | Flavour regulations; artificial almond flavour is usually benzaldehyde | Fewer definite tree-nut flags |
| A facility line after a "Contains:" statement ("Contains: Soy Made in a facility that processes peanuts and tree nuts") | Read as part of the declaration: peanut and tree nuts "declared" (an engine rule, not data) | A cross-contact (may contain) statement | US practice: facility statements are advisory, not FALCPA declarations | Fewer false declarations; still 🔴 in STRICT mode |

## 7. Still open
- **Ingredient order (32 of 20,402 checks, 0.2%).** Rejoining the parsed items in reverse order still changes the verdict on a few labels, mostly OCR text where claims or nutrition figures are mixed into the list. Down from 45 in v0.4; to review case by case (roadmap F-05).
- **Claims on the pack in conflict with the engine** (section 6 of the generated report): the engine contradicts the claim on 30 of 763 vegan products, 65 of 1,311 gluten-free and 98 of 260 lactose-free (mostly milk listed without lactase). Each needs a person: it can be an engine false alarm, a data error (for example soy flour above) or a real labelling issue (roadmap F-05).
- **What this benchmark cannot show:** photos, panels other than the ingredient field, cross-contact, and anything a hand-labelled reference would catch that both references miss (roadmap F-02 and F-19).
