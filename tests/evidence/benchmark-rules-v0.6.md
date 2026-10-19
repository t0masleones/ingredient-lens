# Rules engine benchmark on real products (rules 0.6.1)

6,000 products from Open Food Facts (most scanned in BR, US, FR and DE), 197,300 engine runs, data 653 curated + 35049 Open Food Facts terms (sha256 46f3a9bb9c). Sample: `tests/benchmark/off-products.jsonl` (ODbL). Reproduce: `uv run --directory mcp-server python ../tests/benchmark/run_benchmark.py`.

> [!NOTE]
> **Two references.** A = the allergens Open Food Facts records (broad, but partly derived with the taxonomy this project imports, so an upper bound). B = the manufacturer's own allergen statement when it is in the ingredient text (narrower, independent of those tags). Only the ingredient text is checked: an allergen box printed elsewhere on the pack is invisible here.

## 1. Ingestion: how often the text could be read and split

| Input type | Cases | Ingredient list extracted | Allergen statement found | Gluten statement found (BR) |
|---|---|---|---|---|
| Text (product ingredient field) | 6,000 | 99.9% | 25.0% | 37.0% |
| Recipe (typed list) | 10 golden cases | measured in the golden set only | n/a | n/a |
| Photo | 0 at scale (10 golden cases not run) | **not measured** | **not measured** | **not measured** |

Statements are often missing because the Open Food Facts ingredient field usually stores only the list, not the allergen or gluten box; on a real pack the agent must transcribe every panel. Photo reading, the most common real input, is the largest unmeasured risk (roadmap F-02); the ingestion gate (rule INGEST-GATE) blocks or degrades checks when a reading is unsure.

| Market | Products | Ingredient list extracted | Allergen statement found | Gluten statement found | Any statement found |
|---|---|---|---|---|---|
| BR | 2,000 | 99.7% | 30.3% | 37.0% | 40.4% |
| US | 2,000 | 100.0% | 15.5% | 0.6% | 15.8% |
| FR | 1,000 | 100.0% | 30.5% | 0.1% | 30.6% |
| DE | 1,000 | 99.9% | 27.8% | 0.1% | 27.8% |

## 2. Allergen detection against reference A

Detected = the engine flags the allergen (🔴 or 🟡) for a profile avoiding it.

| Market | Allergen | Declared in reference | Detected | Missed (🟢) | Recall | Recall in STRICT |
|---|---|---|---|---|---|---|
| BR | celery | 11 | 11 | 0 | 100.0% | 100.0% |
| BR | crustacean | 4 | 4 | 0 | 100.0% | 100.0% |
| BR | egg | 181 | 180 | 1 | 99.4% | 99.4% |
| BR | fish | 38 | 38 | 0 | 100.0% | 100.0% |
| BR | gluten | 590 | 590 | 0 | 100.0% | 100.0% |
| BR | milk | 812 | 811 | 1 | 99.9% | 99.9% |
| BR | mollusc | 1 | 1 | 0 | 100.0% | 100.0% |
| BR | mustard | 22 | 22 | 0 | 100.0% | 100.0% |
| BR | peanut | 106 | 106 | 0 | 100.0% | 100.0% |
| BR | sesame | 1 | 1 | 0 | 100.0% | 100.0% |
| BR | soy | 640 | 640 | 0 | 100.0% | 100.0% |
| BR | sulphites | 2 | 2 | 0 | 100.0% | 100.0% |
| BR | tree_nuts | 172 | 172 | 0 | 100.0% | 100.0% |
| DE | celery | 21 | 21 | 0 | 100.0% | 100.0% |
| DE | crustacean | 1 | 1 | 0 | 100.0% | 100.0% |
| DE | egg | 75 | 75 | 0 | 100.0% | 100.0% |
| DE | fish | 8 | 8 | 0 | 100.0% | 100.0% |
| DE | gluten | 384 | 384 | 0 | 100.0% | 100.0% |
| DE | lupin | 10 | 10 | 0 | 100.0% | 100.0% |
| DE | milk | 354 | 352 | 2 | 99.4% | 99.4% |
| DE | mollusc | 1 | 1 | 0 | 100.0% | 100.0% |
| DE | mustard | 52 | 52 | 0 | 100.0% | 100.0% |
| DE | peanut | 51 | 51 | 0 | 100.0% | 100.0% |
| DE | sesame | 36 | 36 | 0 | 100.0% | 100.0% |
| DE | soy | 240 | 240 | 0 | 100.0% | 100.0% |
| DE | sulphites | 3 | 3 | 0 | 100.0% | 100.0% |
| DE | tree_nuts | 175 | 175 | 0 | 100.0% | 100.0% |
| FR | celery | 42 | 42 | 0 | 100.0% | 100.0% |
| FR | crustacean | 1 | 1 | 0 | 100.0% | 100.0% |
| FR | egg | 121 | 121 | 0 | 100.0% | 100.0% |
| FR | fish | 28 | 28 | 0 | 100.0% | 100.0% |
| FR | gluten | 468 | 468 | 0 | 100.0% | 100.0% |
| FR | lupin | 5 | 5 | 0 | 100.0% | 100.0% |
| FR | milk | 389 | 387 | 2 | 99.5% | 99.5% |
| FR | mollusc | 1 | 1 | 0 | 100.0% | 100.0% |
| FR | mustard | 32 | 32 | 0 | 100.0% | 100.0% |
| FR | peanut | 29 | 29 | 0 | 100.0% | 100.0% |
| FR | sesame | 35 | 35 | 0 | 100.0% | 100.0% |
| FR | soy | 192 | 192 | 0 | 100.0% | 100.0% |
| FR | sulphites | 19 | 19 | 0 | 100.0% | 100.0% |
| FR | tree_nuts | 133 | 133 | 0 | 100.0% | 100.0% |
| US | celery | 72 | 72 | 0 | 100.0% | 100.0% |
| US | crustacean | 3 | 3 | 0 | 100.0% | 100.0% |
| US | egg | 134 | 133 | 1 | 99.3% | 99.3% |
| US | fish | 18 | 18 | 0 | 100.0% | 100.0% |
| US | gluten | 592 | 591 | 1 | 99.8% | 99.8% |
| US | milk | 551 | 546 | 5 | 99.1% | 99.1% |
| US | mollusc | 4 | 4 | 0 | 100.0% | 100.0% |
| US | mustard | 39 | 39 | 0 | 100.0% | 100.0% |
| US | peanut | 157 | 157 | 0 | 100.0% | 100.0% |
| US | sesame | 92 | 92 | 0 | 100.0% | 100.0% |
| US | soy | 543 | 543 | 0 | 100.0% | 100.0% |
| US | sulphites | 13 | 13 | 0 | 100.0% | 100.0% |
| US | tree_nuts | 237 | 237 | 0 | 100.0% | 100.0% |
| **All** | | **7,941** | 7,928 | **13** | **99.8%** | **99.8%** |

## 3. Why each miss happened (failure buckets)

Automatic classification with a keyword list independent of the engine's database; the manual review is in `benchmark-review` and agreed with it.

| Bucket | Misses | What it means | Products |
|---|---|---|---|
| Reference definition mismatch | 13 | The allergen is not in the ingredient text: the reference took it from traces, a separate allergen box or a data error | Pão de Fôrma Integral com Ca (egg, BR); Pão de Fôrma Integral com Ca (milk, BR); great grains raisins, dates  (milk, US); Light Rye Crispbread Swedish (milk, US); Organic Garbanzo Beans (gluten, US); Organic Garbanzo Beans (milk, US); Organic Popcorn with Organic (milk, US); Trail Mix (egg, US); White Folded Flatbreads (milk, US); Tartines Craquantes Multi-Cé (milk, FR); Les Fourrées  -  Beurre de C (milk, FR); Brot Mein Knusperbrot Roggen (milk, DE) |
| Ingestion failure | 0 | The ingredient text is unreadable or garbled (OCR) | - |
| Taxonomy or regulation mismatch | 0 | The reference and the regulation or the label disagree (for example coconut as a tree nut; a gluten-free label) | - |
| Engine parsing or vocabulary failure | 0 | The allergen is readable in the text and the engine missed it: a real engine error to fix | - |

## 4. False-alarm proxy: 🔴 for an allergen the reference does not record

Not a true false-positive rate: an allergen missing from reference A is not proof of absence (Open Food Facts tags are incomplete). Each flag is split by whether the independent keyword list sees the allergen in the text: if it does, the reference is incomplete; if not, it may be an engine false alarm (or a word the keyword list lacks) and is read by hand.

| Allergen | Products without it in the reference | Flagged 🔴 | Named in the text | Not named (upper bound on false alarms) |
|---|---|---|---|---|
| celery | 5,845 | 9 (0.2%) | 9 | 0 (0.0%) |
| crustacean | 5,982 | 1 (0.0%) | 0 | 1 (0.0%) |
| egg | 5,480 | 32 (0.6%) | 24 | 8 (0.1%) |
| fish | 5,899 | 16 (0.3%) | 13 | 3 (0.1%) |
| gluten | 3,957 | 224 (5.7%) | 201 | 23 (0.6%) |
| lupin | 5,976 | 5 (0.1%) | 5 | 0 (0.0%) |
| milk | 3,885 | 222 (5.7%) | 211 | 11 (0.3%) |
| mollusc | 5,984 | 7 (0.1%) | 0 | 7 (0.1%) |
| mustard | 5,846 | 23 (0.4%) | 23 | 0 (0.0%) |
| peanut | 5,648 | 20 (0.4%) | 19 | 1 (0.0%) |
| sesame | 5,827 | 52 (0.9%) | 52 | 0 (0.0%) |
| soy | 4,376 | 131 (3.0%) | 122 | 9 (0.2%) |
| sulphites | 5,954 | 97 (1.6%) | 65 | 32 (0.5%) |
| tree_nuts | 5,274 | 105 (2.0%) | 89 | 16 (0.3%) |
| **All** | **75,933** | **944** | **833** | **111 (0.1%)** |

<details>
<summary>Flags with the allergen not named in the text (first 40)</summary>

| Market | Allergen | Product | Why the engine says 🔴 |
|---|---|---|---|
| BR | sulphites | Itaipava (7897395020101) | allergen statement: label declares: contains sulphites |
| BR | mollusc | Mac'n Cheese Cheddar (7891515535193) | MACARRÃO CARACOL DE SÊMOLA: contains mollusc |
| BR | fish | Refrigerante Sem Açúcar Coca Cola Garraf (7894900701609) | CONSERVADOR BENZOATO DE SODIO E ESTABILIZANTE CATO TRISSONCO CONSERVAR 40455G DO SOLE CALOR: contains fish |
| BR | sulphites | Lait De Noix De Coco Traditionnel (7896004400075) | INS 211 e INS 223: contains sulphites |
| BR | sulphites | água De Coco Integral Sococo Caixa 200ml (7896004400358) | sacarose  e antioxidante INS 223: contains sulphites |
| BR | sulphites | Suco de Maçã Integral (7898952578776) | Suco de uva branco integral e antioxidante INS 220: contains sulphites |
| BR | sulphites | Vinagre de vinho tinto (4906309678901) | água filtrada e conservador INS 224: contains sulphites |
| BR | mollusc | Mac'n Cheese Cheddar & Bacon (7891515535186) | MACARRÃO CARACOL DE SÊMOLA: contains mollusc |
| BR | gluten | Hot Bowls Mac'n Cheese Cheddar (7891515606329) | Macarrão Caracol de Sêmola:  |
| BR | mollusc | Hot Bowls Mac'n Cheese Cheddar (7891515606329) | Macarrão Caracol de Sêmola: contains mollusc |
| BR | sulphites | Suco de Uva Tinto Integral (7891737317003) | Suco de uva tinto integral e antioxidante INS 220: contains sulphites |
| BR | egg | Doritos Dinamita Sabor Maionese Chipotle (7892840819392) | composto de palma e soja e preparado para salgadinho sabor maionese e limão picante: contains egg |
| BR | sulphites | Pit Stop Original (7896003706536) | METABISULFITO DE SÓDIO INS 223: contains sulphites |
| BR | sulphites | Sococo coco ralado 50g (7896004400020) | conservador INS 223: contains sulphites |
| BR | sulphites | Leite de Coco (7896004400082) | INS 211 e INS 223: contains sulphites |
| BR | sulphites | Postre cremoso de coco (7896004401386) | Conservadores INS 202 e INS 223: contains sulphites |
| BR | sulphites | Coco em flocos úmido adoçado (7896016600111) | UMECTANTE INS 1520 E CONSERVADOR INS 223: contains sulphites |
| BR | sulphites | Vinagre de Álcool (7896089328240) | Fermentado Acético de Álcool e Conservante INS 224: contains sulphites |
| BR | sulphites | Vinho de Mesa Tinto Suave Quinta do Carv (7896620900805) | conservador INS 202 e antioxidante INS 220 - Responsável Técnico CRQ 5ª 05401513 Graduação Alc.: 10,5% Vol: contains sulphites |
| BR | sulphites | Kero Coco 1L (7896828000239) | antioxidante INS 223: contains sulphites |
| BR | sulphites | Água de coco integral (7896931614941) | ÁGUA DE COCO INTEGRAL E ANTIOXIDANTE INS 223: contains sulphites |
| BR | sulphites |  (7897006310072) | CONSERVADOR INS 223: contains sulphites |
| BR | sulphites | Bolachão de Mel (7897213319714) | metabisulfito de sódio: contains sulphites |
| BR | gluten | Molho barbecue (7897517207571) | molho de soja: may be animal- or plant-derived; allergens not verified (Open Food Facts term) |
| BR | sulphites |  (7898051145732) | allergen statement: label declares: contains sulphites |
| BR | sulphites | Champignons inteiros em conserva (7898075640732) | INS 509) e antioxidante (INS 220: contains sulphites |
| BR | sulphites | Cogumelos Champignon em conserva (7898174850841) | ACIDULANTE ACIDO CÍTRICO E ANTIOXIDANTE DIÓXIDO DE ENXOFRE: contains sulphites |
| BR | sulphites | Leite de Coco Tradicional (7898905356161) | INS 223: contains sulphites |
| BR | sulphites | Leite de coco (7898910048006) | INS 223: contains sulphites |
| BR | sulphites | Suco de Uva Tinto Integral (7898952578141) | INGREDIENȚES: SUCO DE UVA INTEGRAL E ANTIOXIDANTE INS 220: contains sulphites |
| BR | milk | Pão sem queijo (7898957978304) | antiumectante dióxido de silício' e aroma natural vegano sabor parmesão: contains milk |
| BR | milk | RequeVeg Ervas Finas e Pesto (7898958161231) | condimento sabor requeijão: contains milk |
| BR | soy | Discos de Tempê de feijão fradinho (0751320209658) | shoyu macrobiótico pasteurizado: contains soy |
| BR | gluten | Discos de Tempê (0751320209740) | shoyu macrobiótico pasteurizado: Soy sauce usually contains wheat |
| BR | egg | Falafel Vegetariano (2000000162120) | maionese: contains egg |
| US | gluten | SNACK POPPÉ (3245550078674) | SOYA flour:  |
| US | mollusc | PEANUT BUTTER SPREAD (0051500255650) | % DV* Amount/Serving Amount/Serving % DV O Total Fat 16g 20% Total Carb 8g 3% 17% Sat Fat 3.5g Fiber 3g 9% Trans Fat Og Total Sugars 4g Chol |
| US | mollusc | Hide & Seek (8901719117183) | CHOCO CHIPS  [SUGAR: contains mollusc |
| US | sulphites | Robinsons Orange Squash (5000147030125) | sodium metabisulphite: contains sulphites |
| US | sulphites | Nariyal Biscuit (8904422711365) | dough conditioner INS 223: contains sulphites |

</details>

## 5. Reference B: the manufacturer's own allergen statement

Products whose ingredient text includes an allergen statement. The ingredients are checked again **without the statement**, so the engine cannot find an allergen by reading the declaration. Recall: declared allergens the engine flags from the ingredients alone (🔴 or 🟡, as in reference A). Precision: definite (🔴) flags on allergens the market requires that the statement also declares; the rest are labels whose statement leaves the allergen out (XC2: a label error or an engine false alarm, for a person to read).

| Market | Products with a statement | Allergens declared | Flagged from the ingredients alone (recall) | Of which 🔴 | 🔴 flags also declared (precision) | Statements missing a required allergen (XC2) |
|---|---|---|---|---|---|---|
| BR | 591 | 1,240 | 1,226 (98.9%) | 916 | 911 of 978 (93.1%) | 33 (5.6%) |
| US | 236 | 389 | 386 (99.2%) | 349 | 346 of 377 (91.8%) | 23 (9.7%) |
| FR | 9 | 16 | 16 (100.0%) | 10 | 10 of 20 (50.0%) | 5 (55.6%) |
| DE | 9 | 13 | 13 (100.0%) | 13 | 13 of 14 (92.9%) | 0 (0.0%) |

<details>
<summary>Statements missing a required allergen (first 30)</summary>

| Market | Product | What XC2 reports | Ingredient text |
|---|---|---|---|
| BR | Bombom Ferrero Rocher Pacote 37,5g (78909434) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Chocolate ao leite (30%) (açúcar, mantelga de cacau, leite em pó, massa de cacau, emulsificante lecitinas, aromatizante), avelās (28,5%), açücar, óleo |
| BR | Pão Caseiro Milho Panco Pacote 500g (7891203010209) | Ingredients include egg, soy, but the allergen statement does not declare it. | Farinha de trigo enriquecida com ferro e ácido fólico, sêmola de milho&quot;, açúcar, ovo integral, abóbora, glicose de milho, gordura vegetal de palm |
| BR | Ninho Forti+ (7891000284933) | Ingredients include soy, but the allergen statement does not declare it. | Leite em pó integral, fibra (polidextrose), permeado de soro de leite, minerais [cálcio, ferro e zinco], vitaminas [vitamina C, vitamina E, vitamina A |
| BR |  (7622210689573) | Ingredients include soy, but the allergen statement does not declare it. | Massa de cacau, açúcar, manteiga de cacau, emulsificantes lecitina de soja e polirricinoleato de poliglicerol, aromatizante, Contém leite, Pode conter |
| BR | Paçoca (7891118026043) | Ingredients include peanut, but the allergen statement does not declare it. | PT-PACOCA-INGREDIENTES: AMENDOIM, AÇÚCAR, SAL E FÉCULA DE MANDIOCA. ALERGICOS: CONT AMEY DOIM E PODE CONTER LEITE, TRIGO, SOJA, AVEIA, CENTEIO, CEVADA |
| BR | Pão de Mel (7891203020260) | Ingredients include milk, but the allergen statement does not declare it. | INGREDIENTES Farinha de trigo enriquecida com ferro e ácido fólico, açúcar, gordura vegetal, cacau em pó, leite em pó, soro de leite em pó, mel, amido |
| BR | Batata Noisette (7891737234447) | Ingredients include milk, but the allergen statement does not declare it. | Purê de batata, flocos de batata, óleo vegetal de girassol, leite em pó desnatado, sal, pimenta, aromatizante, estabilizantes mono e diglicerideos de  |
| BR | Amendoim Salgado Tipo Japonês (7896058507188) | Ingredients include peanut, but the allergen statement does not declare it. | AMENDOIM, FARINHA DE TRIGO FORTIFICADA COM FERRO E ÁCIDO FÓLICO, ACICAR, SAL MOLHO DE SOJA E MILHO, AMIDO DE MILHO, REAlÇADOR DE SABOR GLUTAMATO MONOS |
| BR | Granola Castanha De Caju Jasmine Pou (7896283007262) | Ingredients include peanut, but the allergen statement does not declare it. | Flocos de aveia integral, melado de cana, açúcar mascavo, óleos vegetais (milho e/ou girassol e /ou algodão e/ou palma), fibra de trigo, castanha-de-c |
| BR | SNICKERS PÉ DE MOLEQUE (7896423497984) | Ingredients include milk, peanut, soy, but the allergen statement does not declare it. | AÇÚCAR, AMENDOIM, XAROPE DE GLICOSE, LEITE EM PÓ, GORDURA DE PALMA, MANTEIGA DE CACAU, MASSA DE CACAU, LACTOSE, GORDURA LÁCTEA, GORDURA VEGETAL, SAL,  |
| BR | Pasta de amendoim com whey (7897685920326) | Ingredients include milk, but the allergen statement does not declare it. | Amendoim torrado moído, proteína isolada de soro de leite (Whey). ALÉRGICOS: CONTÉM _AMENDOIM_. CONTÉM _LACTOSE_. PODE CONTER DERIVADOS DE _SOJA_. |
| BR | Macarrão Instantâneo Talharim Frango (7891079000434) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Ingredientes do Macarrão: farinha de trigo enriquecida com ferro e ácido fólico, gordura vegetal, sal, alho em pó*, reguladores de acidez carbonato de |
| BR | Mortadela de frango (7891164006860) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Carne mecanicamente separada de frango, carne de frango, gordura de frango, água (8,8%), fécula de mandioca (4,4%), proteína de soja (4%) (Agrobacteri |
| BR | Barra de Cereal Morango com Chocolat (7891331010522) | Ingredients include milk, soy, but the allergen statement does not declare it. | cereais (aveia e flocos de cereais), glicose de milho, cobertura sabor chocolate (açúcar, gordura vegetal fracionada, cacau, soro de leite, emulsifica |
| BR | Mortadela Defumada (7891515598259) | Ingredients include tree_nuts, but the allergen statement does not declare it. | CARNE MECANICAMENTE SEPARADA DE FRANGO, CARNE SUÍNA, GORDURA SUINA, CARNE DE FRANGO, ÁGUA (5,60%), AMIDO (4,60%), PROTEÍNA DE SOJA (3,40%)**, PELE SUI |
| BR | Lasanha ao molho de tilápia congelad (7891527064445) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Água, farinha de trigo enriquecida com ferro e ácido fólico, carne mecanicamente separada de tilápia, creme culinário (leite pasteurizado desnatado, s |
| BR | Lasanha de Frango (7891527068108) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Água, farinha de trigo enriquecida com ferro e ácido fólico, peito de frango, polpa de tomate, composto láctea, especiarias (cebola, alho, pimenta pre |
| BR | Doritos Dinamita Sabor Maionese Chip (7892840819392) | Ingredients include egg, but the allergen statement does not declare it. | Milho (Bacillus thuringiensis e Streptomyces viridochromogenes), composto de palma e soja e preparado para salgadinho sabor maionese e limão picante ( |
| BR | Escondidinho Carne Moída Sadia Pacot (7893000052888) | Ingredients include milk, but the allergen statement does not declare it. | AGUA, CARNE BOVINA, BATATA, LEITE INTEGRAL EM PÓ, MARGARINA, MOLHO DE TOMATE, CEBOLA, QUEIJO MUSSARELA, ALHO, AMIDO MODIFICADO, SAL, SALSA, CLORETO DE |
| BR | apresuntado fatiado (7894904268573) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Carne mecanicamente separada de frango, carne suína, carne de frango, gordura suína, amido (4,9%), proteína de soja* (2,3%), sal, açúcar, alho, coentr |
| BR | Molho especial Tarê (7896007865970) | Ingredients include gluten, but the allergen statement does not declare it. | MOLHO DE SOJA (AGUA, SAL, SOJA, MILHO, AÇÚCAR, CORANTE CARAMELO III E CONSERVADOR SORBATO DE POTASSIO), AGUA, AÇÚCAR, XAROPE DE GLICOSE, AMIDO MODIFIC |
| BR | Barra de Cereal Brownie de Chocolate (7896104865903) | Ingredients include milk, soy, but the allergen statement does not declare it. | CEREAIS (FLOCOS DE ARROZ, TRIGO, MILHO E AVEIA), COBERTURA SABOR CHOCOLATE (AÇÚCAR, GORDURA VEGETAL FRACIONADA, SORO DE LEITE EM PÓ, CACAU EM PÓ, LEIT |
| BR | Salgadinho sabor presunto com milho  (7898380412437) | Ingredients include gluten, but the allergen statement does not declare it. | Mix sem glúten (farinha de milho não transgênico e quinoa), óleo vegetal (palma e soja), mix de vitaminas e minerais (vitamina C, ferro, niacina, zinc |
| BR | Peito De Frango Defumado Fatiado Cer (7898907632645) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Carne de Frango, Água 10%, Proteína de Soja 2,5 % (Agrobacterium tumefaciens e Bacillus thuringiensis), Sal, Xarope de Glicose, Açúcar, Extrato de Lev |
| BR | Sonho de Mel (7898910583408) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Farinha de trigo enriquecida com ferro e ácido fólico, água, açúcar cristal, ovos, bicarbonato de sódio, bicarbonato de amônia, sal, cravo em pó, cane |
| BR | Stroopwafel (7898945660051) | Ingredients include egg, but the allergen statement does not declare it. | Farinha de Trigo, Gordura Vegetal, Açúcar, Glicose, Leite em pó, Farinha de Soja, Lecitina de Soja, Ovo em pó, Sal, fermento quimico (Bicarbonato de S |
| BR | Iogurte Vegetal Pasta De Amendoim Vi (7898958161514) | Ingredients include peanut, but the allergen statement does not declare it. | água, base proteica (ervilha e soja não transgênica), açúcar, preparado de amendoim (água, açúcar, aroma idêntico ao natural de amendoim, corante natu |
| BR | Pão Integral Vegano 7 Grãos (7899786900016) | Ingredients include milk, tree_nuts, but the allergen statement does not declare it. | NUTRI-VIDA PÃO O pão nosso de cada dia 7 Grãos INTEGRAL 60,1% 100g 50g %VDM Informação Valor Energético (kcal) 230 114 6 Nutricional Carboidratos Tota |
| BR | Chocolate Ao Leite Com Amendoim (7899970402883) | Ingredients include milk, peanut, but the allergen statement does not declare it. | açúcar, amendoim, massa de cacau, leite em pó integral, manteiga de cacau, gordura vegetal, permeado de soro de leite em pó, soro de leite em pó, gord |
| BR | 100% whey (0602883739697) | Ingredients include gluten, but the allergen statement does not declare it. | Whey Protein Concentrate (WPC), Natural and Artificial Flavor, Xanthan Gum and Sucralose DOES NOT CONTAIN GLUTEN. CONTAINS LACTOSE. ALLERGENS: CONTAIN |

</details>

## 6. Claims on the pack vs the engine

A 🔴 here means the engine found something that contradicts the claim: an engine false alarm, a data error or a real labeling issue. Each one needs a person to look.

| Market | Claim | Products | 🟢 | 🟡 | 🔴 conflict |
|---|---|---|---|---|---|
| BR | gluten | 338 | 36 | 284 | 18 |
| BR | lactose | 104 | 28 | 49 | 27 |
| BR | vegan | 111 | 29 | 73 | 9 |
| DE | gluten | 151 | 3 | 140 | 8 |
| DE | lactose | 86 | 9 | 45 | 32 |
| DE | vegan | 396 | 50 | 339 | 7 |
| FR | gluten | 91 | 1 | 84 | 6 |
| FR | lactose | 17 | 3 | 12 | 2 |
| FR | vegan | 100 | 15 | 81 | 4 |
| US | gluten | 707 | 36 | 641 | 30 |
| US | lactose | 61 | 10 | 13 | 38 |
| US | vegan | 286 | 94 | 181 | 11 |

<details>
<summary>Conflicts (first 30)</summary>

| Market | Claim | Product | Why the engine says 🔴 |
|---|---|---|---|
| BR | lactose | Toddy Light (7894321711058) | LEITE DESNATADO EM PÓ: allergens not verified (Open Food Facts term); SORO DE LEITE EM PÓ: allergens not verified (Open Food Facts term) |
| BR | lactose | Leite UHT Desnatado (7898080640635) | Leite desnatado e estabilizantes citrato de sódio: allergens not verified (Open Food Facts term); allergen statement: label declares: contains milk |
| BR | lactose | IOGURTE BATAVO PENSÉ ZERO MORANGO 1,15KG (7891097103643) | Leite desnatado e/ou leite desnatado reconstituído: allergens not verified (Open Food Facts term); fermentos lácteos e estabilizantes pectinas e agar: may be an |
| BR | gluten | Refrigerante de Guaraná de Baixa Caloria (7891991001373) | allergen statement: label declares: contains gluten |
| BR | lactose | Leite UHT Integral (7892999150124) | Leite integral pasteurizado: allergens not verified (Open Food Facts term) |
| BR | lactose | Light 0% Lactose (7893000502888) | LEITE EM PÓ INTEGRAL SEM LACTOSE: allergens not verified (Open Food Facts term) |
| BR | lactose | Leite desnatado (7896034610031) | Leite desnatado e estabilizantes: allergens not verified (Open Food Facts term); allergen statement: label declares: contains milk |
| BR | lactose | Leite Pó Instantâneo Integral Zero Lacto (7896048706126) | Leite integral: allergens not verified (Open Food Facts term) |
| BR | lactose | Whey Chocolate (7896051166412) | LEITE SEMIDESNATADO E/OU LEITE SEMIDESNATADO RECONSTITUÍDO: allergens not verified (Open Food Facts term); CASEINATO DE CÁLCIO: allergens not verified (Open Foo |
| BR | gluten | Farinha de trigo tipo 1 (7897932900149) | Farinha de Trigo: allergens not verified (Open Food Facts term) |
| BR | gluten | Granola (7898115750292) | flocos de aveia: allergens not verified (Open Food Facts term); gérmen de trigo: allergens not verified (Open Food Facts term) |
| BR | lactose | milico (7891000251638) | Leite desnatado: allergens not verified (Open Food Facts term); soro de leite:  |
| BR | lactose | Creme de Leite Leve (7891000253182) | Creme de leite: ; Leite: ; Lactose: ; Produtos Lácteos: allergens not verified (Open Food Facts term) |
| BR | lactose | Triplo Zero Morango Corpus (7891025114406) | Leite desnatado e/ou leite desnatado reconstituído: allergens not verified (Open Food Facts term); soro de leite em pó: allergens not verified (Open Food Facts  |
| BR | lactose | YoPRO 17g PROTEÍNAS (7891025116943) | Leite desnatado: allergens not verified (Open Food Facts term); soro de leite reconstituído: ; fermentos lácteos: may be animal- or plant-derived; allergens not |
| BR | gluten | Chá Misto de Camomila, Capim-Cidreira, H (7891048038123) | allergen statement: label declares: contains gluten |
| BR | vegan | Pão de mandioquinha e batata sabor queij (7891103220869) | chia e aroma idêntico ao natural de queijo: animal-derived (dairy_rennet) |
| BR | lactose | Requeijão Cremoso Light Vigor Pote 500g (7891999010070) | Leite desnatado: allergens not verified (Open Food Facts term); creme de leite:  |
| BR | gluten | Arroz Tio João 7 Grãos Integrais 500g (7893500045434) | aveia: Gluten source in Brazil; often cross-contaminated; cevada:  |
| BR | lactose | Cappuccino Solúvel Zero Lactose 3 Coraçõ (7896005808016) | leite em pó integral: allergens not verified (Open Food Facts term); leite em pó desnatado: allergens not verified (Open Food Facts term); lactose: ; leite inte |
| BR | gluten | Arroz Sete Grãos+ (7896038300013) | aveia: Gluten source in Brazil; often cross-contaminated; cevada:  |
| BR | lactose | Achocolatado Itambé Zero Lactose (7896051128045) | Soro de leite elou soro de leite em pó reconstituído: allergens not verified (Open Food Facts term); leite integral elou leite em pó integral reconstituído: all |
| BR | gluten | Macarrão De Sêmola Com Ovos Espaguetinho (7896205788033) | Farinha de trigo: allergens not verified (Open Food Facts term) |
| BR | lactose | Pasta de Amendoim Integral Chocolate Bra (7896256066043) | leite em pó: allergens not verified (Open Food Facts term) |
| BR | gluten | Granola Cereais Maltados Jasmine Pouch 2 (7896283000430) | Flocos de aveia integral: allergens not verified (Open Food Facts term); extrato de malte: Usually barley; fibra de trigo:  |
| BR | gluten | Granola Premium Tradicional (7896333039465) | aveia laminada: Gluten source in Brazil; often cross-contaminated |
| BR | gluten | Granola Frutas e Mel Sem Adição de Açúca (7896496972104) | Aveia: Gluten source in Brazil; often cross-contaminated |
| BR | gluten | Granola Banana E Cacau Mãe Terra Pacote  (7896496972203) | 71,2%: aveia prensada integral: Gluten source in Brazil; often cross-contaminated; flocos integrais de trigo: ; fibra de aveia: allergens not verified (Open Foo |
| BR | vegan | Manteiga de coco sabor manteiga sem sal  (7896552906708) | aromatizante idêntico ao natural de manteiga: animal-derived (dairy) |
| BR | lactose | Leite UHT Integral (7896775400052) | Leite integral: allergens not verified (Open Food Facts term) |

</details>

## 7. Coverage: ingredients found in the database

| Market | Ingredients | Found | Coverage | Most frequent unknown items |
|---|---|---|---|---|
| BR | 20,566 | 19,264 | 93.7% | agrobacterium tumefaciens (44), bacillus thuringiensis (43), streptomyces viridochromogenes (40), minerais (23), zea mays (21), poliglicerol polirricinoleato (19), agrobacterium sp (17), e (17), segurelha (15), a (14), l (13), sphingobium herbicidovorans (11) |
| US | 28,686 | 27,564 | 96.1% | processed with alkali (32), a b vitamin (27), to preserve freshness (26), yellow 5 (23), yellow 6 (19), palmitate (18), blue 1 (17), to maintain freshness (16), red 40 (15), for freshness (14), mineral nutrients (13), almondmilk (12) |
| FR | 12,019 | 11,627 | 96.7% | bouillon (22), b9 (21), presence naturelle de polyphenols (20), e (15), origine : france (14), d (13), origine france (9), origine: france (9), mais (9), mineraux (8), riboflavine (8), pp (7) |
| DE | 14,791 | 13,653 | 92.3% | mais (24), natriumhydrogencarbonat (23), tomatenpulver (22), paprikapulver (21), paprikaextrakt (14), d (13), a (12), ackerbohnenmehl (12), tricalciumphosphat (11), tricalciumcitrat (10), in veranderlichen gewichtsanteilen (10), natriumcyclamat (10) |

## 8. Metamorphic tests (properties that must hold for any label)

| Property | Checks | Failures |
|---|---|---|
| STRICT is never milder | 25,914 | 0 |
| adding 'may contain milk' never improves a milk verdict | 5,991 | 0 |
| ingredient order does not change the verdict | 25,248 | 32 |
| same input, same verdict | 25,914 | 0 |
| upper case does not change the verdict | 25,914 | 0 |

Examples of failures, ingredient order does not change the verdict:
- 7891103221255 (lactose): Farinha de arroz, amido de milho, banana em flocos, vitaminas e minerais zinco), vitamina A (palmitato de retinila), vit
- 7891103221255 (milk): Farinha de arroz, amido de milho, banana em flocos, vitaminas e minerais zinco), vitamina A (palmitato de retinila), vit
- 7896009301155 (lactose): Atum, óleo vegetal de soja, água, sal e extrato vegetal em pó (extratos de soja, cenoura e batata), Sem conservantes, Fo
- 7896714803241 (lactose): Leite e/ou leite em pó integral reconstituído, açúcar, soro de leite e/ou soro de leite em pó reconstituido, glicose, am
- 7896714803241 (vegan): Leite e/ou leite em pó integral reconstituído, açúcar, soro de leite e/ou soro de leite em pó reconstituido, glicose, am

## 9. Performance

197,300 engine runs: median 4.6 ms, 95th percentile 17.1 ms per label.
