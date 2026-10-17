# Rules engine benchmark on real products (rules 0.6.0)

6,000 products from Open Food Facts (most scanned in BR, US, FR and DE), 167,314 engine runs, data 644 curated + 35051 Open Food Facts terms (sha256 d9d2171dfc). Sample: `tests/benchmark/off-products.jsonl` (ODbL). Reproduce: `uv run --directory mcp-server python ../tests/benchmark/run_benchmark.py`.

> [!NOTE]
> **Two references.** A = the allergens Open Food Facts records (broad, but partly derived with the taxonomy this project imports, so an upper bound). B = the manufacturer's own allergen statement when it is in the ingredient text (narrower, independent of those tags). Only the ingredient text is checked: an allergen box printed elsewhere on the pack is invisible here.

## 1. Ingestion: how often the text could be read and split

| Input type | Cases | Ingredient list extracted | Allergen statement found | Gluten statement found (BR) |
|---|---|---|---|---|
| Text (product ingredient field) | 6,000 | 99.9% | 19.0% | 27.0% |
| Recipe (typed list) | 10 golden cases | measured in the golden set only | n/a | n/a |
| Photo | 0 at scale (10 golden cases not run) | **not measured** | **not measured** | **not measured** |

Statements are often missing because the Open Food Facts ingredient field usually stores only the list, not the allergen or gluten box; on a real pack the agent must transcribe every panel. Photo reading, the most common real input, is the largest unmeasured risk (roadmap F-02); the ingestion gate (rule INGEST-GATE) blocks or degrades checks when a reading is unsure.

| Market | Products | Ingredient list extracted | Allergen statement found | Gluten statement found | Any statement found |
|---|---|---|---|---|---|
| BR | 2,000 | 99.8% | 24.2% | 27.0% | 32.3% |
| US | 2,000 | 99.9% | 12.9% | 0.4% | 13.2% |
| FR | 1,000 | 100.0% | 23.5% | 0.6% | 23.8% |
| DE | 1,000 | 100.0% | 16.3% | 1.0% | 17.1% |

## 2. Allergen detection against reference A

Detected = the engine flags the allergen (🔴 or 🟡) for a profile avoiding it.

| Market | Allergen | Declared in reference | Detected | Missed (🟢) | Recall | Recall in STRICT |
|---|---|---|---|---|---|---|
| BR | celery | 9 | 9 | 0 | 100.0% | 100.0% |
| BR | crustacean | 1 | 1 | 0 | 100.0% | 100.0% |
| BR | egg | 39 | 39 | 0 | 100.0% | 100.0% |
| BR | fish | 11 | 11 | 0 | 100.0% | 100.0% |
| BR | gluten | 218 | 217 | 1 | 99.5% | 99.5% |
| BR | milk | 165 | 165 | 0 | 100.0% | 100.0% |
| BR | mollusc | 1 | 1 | 0 | 100.0% | 100.0% |
| BR | mustard | 5 | 5 | 0 | 100.0% | 100.0% |
| BR | peanut | 39 | 39 | 0 | 100.0% | 100.0% |
| BR | sesame | 1 | 1 | 0 | 100.0% | 100.0% |
| BR | soy | 225 | 225 | 0 | 100.0% | 100.0% |
| BR | sulphites | 13 | 13 | 0 | 100.0% | 100.0% |
| BR | tree_nuts | 35 | 35 | 0 | 100.0% | 100.0% |
| DE | celery | 19 | 19 | 0 | 100.0% | 100.0% |
| DE | crustacean | 3 | 2 | 1 | 66.7% | 66.7% |
| DE | egg | 72 | 71 | 1 | 98.6% | 98.6% |
| DE | fish | 25 | 24 | 1 | 96.0% | 96.0% |
| DE | gluten | 289 | 289 | 0 | 100.0% | 100.0% |
| DE | lupin | 3 | 3 | 0 | 100.0% | 100.0% |
| DE | milk | 320 | 317 | 3 | 99.1% | 99.1% |
| DE | mustard | 31 | 31 | 0 | 100.0% | 100.0% |
| DE | peanut | 35 | 35 | 0 | 100.0% | 100.0% |
| DE | sesame | 16 | 15 | 1 | 93.8% | 93.8% |
| DE | soy | 194 | 194 | 0 | 100.0% | 100.0% |
| DE | sulphites | 28 | 28 | 0 | 100.0% | 100.0% |
| DE | tree_nuts | 132 | 132 | 0 | 100.0% | 100.0% |
| FR | celery | 42 | 42 | 0 | 100.0% | 100.0% |
| FR | crustacean | 3 | 3 | 0 | 100.0% | 100.0% |
| FR | egg | 86 | 86 | 0 | 100.0% | 100.0% |
| FR | fish | 21 | 21 | 0 | 100.0% | 100.0% |
| FR | gluten | 408 | 407 | 1 | 99.8% | 99.8% |
| FR | lupin | 4 | 4 | 0 | 100.0% | 100.0% |
| FR | milk | 316 | 311 | 5 | 98.4% | 98.4% |
| FR | mustard | 22 | 22 | 0 | 100.0% | 100.0% |
| FR | peanut | 36 | 36 | 0 | 100.0% | 100.0% |
| FR | sesame | 21 | 21 | 0 | 100.0% | 100.0% |
| FR | soy | 181 | 181 | 0 | 100.0% | 100.0% |
| FR | sulphites | 17 | 17 | 0 | 100.0% | 100.0% |
| FR | tree_nuts | 120 | 119 | 1 | 99.2% | 99.2% |
| US | celery | 37 | 37 | 0 | 100.0% | 100.0% |
| US | egg | 67 | 66 | 1 | 98.5% | 98.5% |
| US | fish | 15 | 15 | 0 | 100.0% | 100.0% |
| US | gluten | 346 | 344 | 2 | 99.4% | 99.4% |
| US | milk | 326 | 322 | 4 | 98.8% | 98.8% |
| US | mollusc | 6 | 6 | 0 | 100.0% | 100.0% |
| US | mustard | 20 | 20 | 0 | 100.0% | 100.0% |
| US | peanut | 103 | 103 | 0 | 100.0% | 100.0% |
| US | sesame | 37 | 37 | 0 | 100.0% | 100.0% |
| US | soy | 261 | 261 | 0 | 100.0% | 100.0% |
| US | sulphites | 15 | 15 | 0 | 100.0% | 100.0% |
| US | tree_nuts | 168 | 168 | 0 | 100.0% | 100.0% |
| **All** | | **4,607** | 4,585 | **22** | **99.5%** | **99.5%** |

## 3. Why each miss happened (failure buckets)

Automatic classification with a keyword list independent of the engine's database; the manual review is in `benchmark-review` and agreed with it.

| Bucket | Misses | What it means | Products |
|---|---|---|---|
| Reference definition mismatch | 20 | The allergen is not in the ingredient text: the reference took it from traces, a separate allergen box or a data error | great grains raisins, dates  (milk, US); Light Rye Crispbread Swedish (milk, US); Organic Garbanzo Beans (gluten, US); Organic Garbanzo Beans (milk, US); Organic Popcorn with Organic (milk, US); Tortilla Wraps (gluten, US); Omega-3 Trail Mix (egg, US); Cacao céréales (milk, FR); Chicoree soluble nature bio  (gluten, FR); Les Fourrées  -  Beurre de C (milk, FR); Tartines Craquantes Multi-Cé (milk, FR); Saveir Sel & Vinaigre (milk, FR) |
| Ingestion failure | 0 | The ingredient text is unreadable or garbled (OCR) | - |
| Taxonomy or regulation mismatch | 2 | The reference and the regulation or the label disagree (for example coconut as a tree nut; a gluten-free label) | Paçoquita 3,84 GR. (gluten, BR); Natural Coconut Cream (tree_nuts, FR) |
| Engine parsing or vocabulary failure | 0 | The allergen is readable in the text and the engine missed it: a real engine error to fix | - |

## 4. False-alarm proxy: 🔴 for an allergen the reference does not record

Not a true false-positive rate: an allergen missing from reference A is not proof of absence (Open Food Facts tags are incomplete). Each flag is split by whether the independent keyword list sees the allergen in the text: if it does, the reference is incomplete; if not, it may be an engine false alarm (or a word the keyword list lacks) and is read by hand.

| Allergen | Products without it in the reference | Flagged 🔴 | Named in the text | Not named (upper bound on false alarms) |
|---|---|---|---|---|
| celery | 5,886 | 40 (0.7%) | 39 | 1 (0.0%) |
| crustacean | 5,986 | 5 (0.1%) | 2 | 3 (0.1%) |
| egg | 5,729 | 152 (2.7%) | 134 | 18 (0.3%) |
| fish | 5,921 | 52 (0.9%) | 37 | 15 (0.3%) |
| gluten | 4,732 | 712 (15.0%) | 693 | 19 (0.4%) |
| lupin | 5,986 | 8 (0.1%) | 8 | 0 (0.0%) |
| milk | 4,866 | 862 (17.7%) | 849 | 13 (0.3%) |
| mollusc | 5,986 | 39 (0.7%) | 35 | 4 (0.1%) |
| mustard | 5,915 | 44 (0.7%) | 44 | 0 (0.0%) |
| peanut | 5,780 | 125 (2.2%) | 121 | 4 (0.1%) |
| sesame | 5,918 | 91 (1.5%) | 91 | 0 (0.0%) |
| soy | 5,132 | 569 (11.1%) | 538 | 31 (0.6%) |
| sulphites | 5,920 | 102 (1.7%) | 55 | 47 (0.8%) |
| tree_nuts | 5,538 | 238 (4.3%) | 195 | 43 (0.8%) |
| **All** | **79,295** | **3,039** | **2,841** | **198 (0.2%)** |

<details>
<summary>Flags with the allergen not named in the text (first 40)</summary>

| Market | Allergen | Product | Why the engine says 🔴 |
|---|---|---|---|
| BR | peanut | Barra Aveia & Cereais Chocolate Preto &  (5607047020869) | amendoins: contains peanut |
| BR | sulphites | Suco de Uva (7891141019838) | antioxidante INS 220: contains sulphites |
| BR | tree_nuts | Avellana (7701362014904) | saborizante artificial a Avellana: contains tree_nuts |
| BR | tree_nuts | Barras de Cereal Avellanas (7804000002049) | avellanas europeas 7%: contains tree_nuts |
| BR | egg | Biothentic Riz Long 1 / 2 Complet 1Kg (3760092212657) | de lait et d'oeuf: contains egg |
| BR | tree_nuts | Biothentic Riz Long 1 / 2 Complet 1Kg (3760092212657) | de fruits à coques: contains tree_nuts |
| BR | sulphites | Itaipava (7897395020101) | allergen statement: label declares: contains sulphites |
| BR | soy | Chocolate Mousse De Maracujá Snickers Pa (7896423456561) | emulgator: e322 lecitina de soia: contains soy |
| BR | tree_nuts | Alfajores Mixtos (7791875000013) | esencia artificial de almendra: contains tree_nuts |
| BR | crustacean | Vainilla (7802410545323) | crustáceos: contains crustacean |
| BR | tree_nuts | Vainilla (7802410545323) | moluscos y almendras: contains tree_nuts |
| BR | mollusc | Mac'n Cheese Cheddar (7891515535193) | MACARRÃO CARACOL DE SÊMOLA: contains mollusc |
| BR | tree_nuts | Havannets Chocolate (7791875000471) | esencia artificial de almendra: contains tree_nuts |
| BR | fish | Refrigerante Sem Açúcar Coca Cola Garraf (7894900701609) | CONSERVADOR BENZOATO DE SODIO E ESTABILIZANTE CATO TRISSONCO CONSERVAR 40455G DO SOLE CALOR: contains fish |
| BR | tree_nuts | BARRA DE CEREAL (7804673910535) | pasta de almendra 10%: contains tree_nuts; almendra laminada: contains tree_nuts |
| BR | fish | Cookies Special Selection (5601069102961) | noix de coco râpé: contains fish |
| BR | sulphites | Suco de Maçã Integral (7898952578776) | Suco de uva branco integral e antioxidante INS 220: contains sulphites |
| BR | tree_nuts | GRANOLA (7802000017834) | almendras fileteadas: contains tree_nuts |
| BR | sulphites | água De Coco Integral Sococo Caixa 200ml (7896004400358) | sacarose  e antioxidante INS 223: contains sulphites |
| BR | sulphites | Lait De Noix De Coco Traditionnel (7896004400075) | INS 211 e INS 223: contains sulphites |
| BR | sulphites | Coco Ralado Desidratado (7896004400013) | Conservador INS 223: contains sulphites |
| BR | fish | ATÚN LOMITOS en Agua (7804621471019) | Atún: contains fish; allergen statement: label declares: contains fish |
| BR | fish | ATÚN LOMITOS (7804621471781) | Atún: contains fish; allergen statement: label declares: contains fish |
| BR | fish | JUREL (7801528000175) | allergen statement: label declares: contains fish |
| BR | sulphites | Coco em flocos úmido adoçado (7896016600111) | UMECTANTE INS 1520 E CONSERVADOR INS 223: contains sulphites |
| BR | fish | SARDINAS EN TOMATE (7801534002330) | Sardinas: contains fish |
| BR | sulphites | Suco de uva tinto integral (7896034300819) | antioxidante INS 220: contains sulphites |
| BR | tree_nuts | Pan de PASCUA (7803495001780) | nueces: contains tree_nuts; almendras: contains tree_nuts |
| BR | sulphites | Vinagre de vinho tinto (4906309678901) | água filtrada e conservador INS 224: contains sulphites |
| BR | fish | ATÚN LOMITOS EN AGUA (0400001143162) | Lomitos de atún: contains fish |
| BR | tree_nuts | ALMENDRAS NATURALES (0400050283727) | Almendras naturales: contains tree_nuts |
| BR | tree_nuts | GRANOLA (0799192229930) | nuez: contains tree_nuts |
| BR | tree_nuts |  (0750894671267) | ALMENDRAS: contains tree_nuts; allergen statement: label declares: contains tree_nuts |
| BR | tree_nuts | TOBLERONE (7622300986636) | almendras: contains tree_nuts |
| BR | egg | Farandole de madeleine (00000022) | œufs de poules élevées en plein air 14.5%: contains egg |
| BR | sulphites | Bolachão de Mel (7897213319714) | metabisulfito de sódio: contains sulphites |
| BR | sulphites | Damasco seco (7895000529162) | conservador dióxido de enxofre: contains sulphites |
| BR | soy | Distração baunilha e chocolate (7896003702606) | EMULSIFER SOYBEAN LECITHIN: contains soy |
| BR | sulphites | Distração baunilha e chocolate (7896003702606) | SODIUM METABISULPHITE: contains sulphites |
| BR | sulphites | Pit Stop (7896003706543) | SODIUM METABISULPHITE: contains sulphites |

</details>

## 5. Reference B: the manufacturer's own allergen statement

Products whose ingredient text includes an allergen statement. The ingredients are checked again **without the statement**, so the engine cannot find an allergen by reading the declaration. Recall: declared allergens the engine flags from the ingredients alone (🔴 or 🟡, as in reference A). Precision: definite (🔴) flags on allergens the market requires that the statement also declares; the rest are labels whose statement leaves the allergen out (XC2: a label error or an engine false alarm, for a person to read).

| Market | Products with a statement | Allergens declared | Flagged from the ingredients alone (recall) | Of which 🔴 | 🔴 flags also declared (precision) | Statements missing a required allergen (XC2) |
|---|---|---|---|---|---|---|
| BR | 457 | 882 | 871 (98.8%) | 664 | 660 of 714 (92.4%) | 26 (5.7%) |
| US | 172 | 289 | 284 (98.3%) | 253 | 249 of 272 (91.5%) | 18 (10.5%) |
| FR | 5 | 12 | 12 (100.0%) | 6 | 6 of 8 (75.0%) | 1 (20.0%) |
| DE | 11 | 13 | 13 (100.0%) | 13 | 13 of 20 (65.0%) | 3 (27.3%) |

<details>
<summary>Statements missing a required allergen (first 30)</summary>

| Market | Product | What XC2 reports | Ingredient text |
|---|---|---|---|
| BR | Bombom Ferrero Rocher Pacote 37,5g (78909434) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Chocolate ao leite (30%) (açúcar, mantelga de cacau, leite em pó, massa de cacau, emulsificante lecitinas, aromatizante), avelās (28,5%), açücar, óleo |
| BR | Pão Caseiro Milho Panco Pacote 500g (7891203010209) | Ingredients include egg, soy, but the allergen statement does not declare it. | Farinha de trigo enriquecida com ferro e ácido fólico, sêmola de milho&quot;, açúcar, ovo integral, abóbora, glicose de milho, gordura vegetal de palm |
| BR | Quero Mostarda (7896102509144) | Ingredients include milk, but the allergen statement does not declare it. | Agua, vinagre, açúcar invertido, farinha de mostarda, creme de milho, amido modificado, sal, corante cúrcuma, estabilizantes goma xantana e goma guar, |
| BR | Ninho Forti+ (7891000284933) | Ingredients include soy, but the allergen statement does not declare it. | Leite em pó integral, fibra (polidextrose), permeado de soro de leite, minerais [cálcio, ferro e zinco], vitaminas [vitamina C, vitamina E, vitamina A |
| BR | Batata Noisette (7891737234447) | Ingredients include milk, but the allergen statement does not declare it. | Purê de batata, flocos de batata, óleo vegetal de girassol, leite em pó desnatado, sal, pimenta, aromatizante, estabilizantes mono e diglicerideos de  |
| BR | Pão de Mel (7891203020260) | Ingredients include milk, but the allergen statement does not declare it. | INGREDIENTES Farinha de trigo enriquecida com ferro e ácido fólico, açúcar, gordura vegetal, cacau em pó, leite em pó, soro de leite em pó, mel, amido |
| BR | Paçoca (7891118026043) | Ingredients include peanut, but the allergen statement does not declare it. | PT-PACOCA-INGREDIENTES: AMENDOIM, AÇÚCAR, SAL E FÉCULA DE MANDIOCA. ALERGICOS: CONT AMEY DOIM E PODE CONTER LEITE, TRIGO, SOJA, AVEIA, CENTEIO, CEVADA |
| BR | Ovo De Chocolate Ao Leite Oreo Lacta (7622201684525) | Ingredients include egg, but the allergen statement does not declare it. | OVO DE CHOCOLATE AO LEITE COM RECHEIO CREMOSO E BISCOITO INGR: AÇÚCAR, GORDURA VEGETAL, LEITE EM PO DESNATADO, MASSA DE CACAU, ÓLEO VEGETAL, MANTEIGA  |
| BR |  (7622210689573) | Ingredients include soy, but the allergen statement does not declare it. | Massa de cacau, açúcar, manteiga de cacau, emulsificantes lecitina de soja e polirricinoleato de poliglicerol, aromatizante, Contém leite, Pode conter |
| BR | Granola Castanha De Caju Jasmine Pou (7896283007262) | Ingredients include peanut, but the allergen statement does not declare it. | Flocos de aveia integral, melado de cana, açúcar mascavo, óleos vegetais (milho e/ou girassol e /ou algodão e/ou palma), fibra de trigo, castanha-de-c |
| BR | SNICKERS PÉ DE MOLEQUE (7896423497984) | Ingredients include milk, peanut, soy, but the allergen statement does not declare it. | AÇÚCAR, AMENDOIM, XAROPE DE GLICOSE, LEITE EM PÓ, GORDURA DE PALMA, MANTEIGA DE CACAU, MASSA DE CACAU, LACTOSE, GORDURA LÁCTEA, GORDURA VEGETAL, SAL,  |
| BR | Amendoim Salgado Tipo Japonês (7896058507188) | Ingredients include peanut, but the allergen statement does not declare it. | AMENDOIM, FARINHA DE TRIGO FORTIFICADA COM FERRO E ÁCIDO FÓLICO, ACICAR, SAL MOLHO DE SOJA E MILHO, AMIDO DE MILHO, REAlÇADOR DE SABOR GLUTAMATO MONOS |
| BR | Pasta de amendoim com whey (7897685920326) | Ingredients include milk, but the allergen statement does not declare it. | Amendoim torrado moído, proteína isolada de soro de leite (Whey). ALÉRGICOS: CONTÉM _AMENDOIM_. CONTÉM _LACTOSE_. PODE CONTER DERIVADOS DE _SOJA_. |
| BR | Molho especial Tarê (7896007865970) | Ingredients include gluten, but the allergen statement does not declare it. | MOLHO DE SOJA (AGUA, SAL, SOJA, MILHO, AÇÚCAR, CORANTE CARAMELO III E CONSERVADOR SORBATO DE POTASSIO), AGUA, AÇÚCAR, XAROPE DE GLICOSE, AMIDO MODIFIC |
| BR | Mortadela de frango (7891164006860) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Carne mecanicamente separada de frango, carne de frango, gordura de frango, água (8,8%), fécula de mandioca (4,4%), proteína de soja (4%) (Agrobacteri |
| BR | BROWNIE MANÍ (0725765444912) | Ingredients include milk, but the allergen statement does not declare it. | Dátil, proteína aislada de suero de leche, fibra de achicoria, crisp de proteína de soya, mantequilla de maní, chocolate bitter 60% cacao sin azúcar ( |
| BR | LIGHT MAYO (0021000070268) | Ingredients include soy, but the allergen statement does not declare it. | AGUA, ACEITE DE SOYA, ALMIDÓN MODIFICADO DE MAÍZ*, VINAGRE, AZÚCAR, MALTODEXTRINA, SAL, SABOR NATURAL, HUEVO PASTEURIZADO, HARINA DE MOSTAZA, ÁCIDO LÁ |
| BR | Sonho de Mel (7898910583408) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Farinha de trigo enriquecida com ferro e ácido fólico, água, açúcar cristal, ovos, bicarbonato de sódio, bicarbonato de amônia, sal, cravo em pó, cane |
| BR | Barra de Cereal Morango com Chocolat (7891331010522) | Ingredients include milk, soy, but the allergen statement does not declare it. | cereais (aveia e flocos de cereais), glicose de milho, cobertura sabor chocolate (açúcar, gordura vegetal fracionada, cacau, soro de leite, emulsifica |
| BR | Mortadela Defumada (7891515598259) | Ingredients include tree_nuts, but the allergen statement does not declare it. | CARNE MECANICAMENTE SEPARADA DE FRANGO, CARNE SUÍNA, GORDURA SUINA, CARNE DE FRANGO, ÁGUA (5,60%), AMIDO (4,60%), PROTEÍNA DE SOJA (3,40%)**, PELE SUI |
| BR | Lasanha ao molho de tilápia congelad (7891527064445) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Água, farinha de trigo enriquecida com ferro e ácido fólico, carne mecanicamente separada de tilápia, creme culinário (leite pasteurizado desnatado, s |
| BR | Stroopwafel (7898945660051) | Ingredients include egg, but the allergen statement does not declare it. | Farinha de Trigo, Gordura Vegetal, Açúcar, Glicose, Leite em pó, Farinha de Soja, Lecitina de Soja, Ovo em pó, Sal, fermento quimico (Bicarbonato de S |
| BR | Pão Croissant (7908073101538) | Ingredients include gluten, but the allergen statement does not declare it. | PÃO CROISSANT ngredientes: Farinha de trigo enriquecida com ferro margarina, leite em pó Integral, sal e Conservador propionato de cálcio, ALERGICOS:  |
| BR | Chocolate Ao Leite Com Amendoim (7899970402883) | Ingredients include milk, peanut, but the allergen statement does not declare it. | açúcar, amendoim, massa de cacau, leite em pó integral, manteiga de cacau, gordura vegetal, permeado de soro de leite em pó, soro de leite em pó, gord |
| BR | Macarrão Instantâneo Talharim Frango (7891079000434) | Ingredients include tree_nuts, but the allergen statement does not declare it. | Ingredientes do Macarrão: farinha de trigo enriquecida com ferro e ácido fólico, gordura vegetal, sal, alho em pó*, reguladores de acidez carbonato de |
| BR | Escondidinho Carne Moída Sadia Pacot (7893000052888) | Ingredients include milk, but the allergen statement does not declare it. | AGUA, CARNE BOVINA, BATATA, LEITE INTEGRAL EM PÓ, MARGARINA, MOLHO DE TOMATE, CEBOLA, QUEIJO MUSSARELA, ALHO, AMIDO MODIFICADO, SAL, SALSA, CLORETO DE |
| US | Mayonnaise recette originale (6111184004129) | Ingredients include egg, soy, but the allergen statement does not declare it. | Huile de soja, eau, vinaigre de table, jaune d’œufs, moutarde&quot;, sel, stabilisants (E412, E415), conservateur : (E202, E211) et antioxydant : E330 |
| US | Activia Céréales (6111032002208) | Ingredients include milk, but the allergen statement does not declare it. | Lait sans crème, mélanges de produits laitiers, préparations céréalières, crème, sucre, lait en poudre sans crème, amidon modifié, arômes, levure helb |
| US | Ramen Noodle Soup Chicken Flavor (0041789002113) | Ingredients include milk, but the allergen statement does not declare it. | ENRICHED WHEAT FLOUR (WHEAT FLOUR, NIACIN, REDUCED IRON, THIAMINE MONONITRAT RIBOFLAVIN, FOLIC ACID), VEGETABLE OIL (CONTAINS ONE OR MORE OF THE FOLLO |
| US | Multi-Grain 6-Seed Crunchy, Baked Ri (0879890002995) | Ingredients include gluten, but the allergen statement does not declare it. | Brown rice flour, sesame seeds, potato starch, flax seeds, olive oil, amaranth seeds, quinoa seeds, chia seeds, sea salt, tamari soy sauce powder (tam |

</details>

## 6. Claims on the pack vs the engine

A 🔴 here means the engine found something that contradicts the claim: an engine false alarm, a data error or a real labeling issue. Each one needs a person to look.

| Market | Claim | Products | 🟢 | 🟡 | 🔴 conflict |
|---|---|---|---|---|---|
| BR | gluten | 382 | 74 | 283 | 25 |
| BR | lactose | 100 | 35 | 36 | 29 |
| BR | vegan | 126 | 61 | 59 | 6 |
| DE | gluten | 178 | 11 | 158 | 9 |
| DE | lactose | 66 | 5 | 35 | 26 |
| DE | vegan | 220 | 68 | 145 | 7 |
| FR | gluten | 125 | 6 | 112 | 7 |
| FR | lactose | 30 | 2 | 21 | 7 |
| FR | vegan | 127 | 25 | 94 | 8 |
| US | gluten | 626 | 42 | 560 | 24 |
| US | lactose | 64 | 10 | 18 | 36 |
| US | vegan | 290 | 103 | 178 | 9 |

<details>
<summary>Conflicts (first 30)</summary>

| Market | Claim | Product | Why the engine says 🔴 |
|---|---|---|---|
| BR | gluten | Tapioca Hidratada da Terrinha 500g (7898994081623) | allergen statement: label declares: contains gluten |
| BR | gluten | Herdade Do Esporão Extra Virgem (5601989003126) | 100% azeite de oliva extravirgem Sem alergênios Vegan Sem glúten Sem conservantes Produto artesanal Sem aditivos Orgânico:  |
| BR | lactose | Toddy Light (7894321711058) | LEITE DESNATADO EM PÓ: allergens not verified (Open Food Facts term); SORO DE LEITE EM PÓ: allergens not verified (Open Food Facts term) |
| BR | lactose | Leite UHT Desnatado (7898080640635) | Leite desnatado e estabilizantes citrato de sódio: allergens not verified (Open Food Facts term); allergen statement: label declares: contains milk |
| BR | gluten | Pão Integral Maçã, Canela E Passas Wickb (7896066304571) | Farinha de trigo integral: allergens not verified (Open Food Facts term); farinha de trigo enriquecida com ferro e ácido fólico: allergens not verified (Open Fo |
| BR | gluten | Quero Mostarda (7896102509144) | allergen statement: label declares: contains gluten |
| BR | lactose | Quero Mostarda (7896102509144) | creme de milho: allergens not verified (Open Food Facts term) |
| BR | lactose | Iogurte Desnatado com Preparo de Morango (7891097103643) | Leite desnatado e/ou leite desnatado reconstituído: allergens not verified (Open Food Facts term); fermentos lácteos e estabilizantes pectinas e agar: may be an |
| BR | lactose | Iogurte com creme e calda de frutas (7891999010735) | Leite desnatado e/ou leite desnatado reconstituido: allergens not verified (Open Food Facts term); concentrado proteico de leite: ; creme de leite: ; allergen s |
| BR | gluten | Refrigerante de Guaraná de Baixa Caloria (7891991001373) | allergen statement: label declares: contains gluten |
| BR | gluten | Galletitas de arroz (7804646450273) | allergen statement: label declares: contains gluten |
| BR | vegan | BARRA DE CEREAL (7804673910535) | limón en polvo 3%: animal-derived (slaughter) |
| BR | lactose | Light 0% Lactose (7893000502888) | LEITE EM PÓ INTEGRAL SEM LACTOSE: allergens not verified (Open Food Facts term) |
| BR | lactose | Leite UHT Integral (7892999150124) | Leite integral pasteurizado: allergens not verified (Open Food Facts term) |
| BR | gluten | Aveia Em Flocos grossos Vitalin Pouch 20 (7898568900688) | Aveia em Flocos Grossos: Gluten source in Brazil; often cross-contaminated |
| BR | lactose | Leite Integral UHT (7896122305207) | Leite integral: allergens not verified (Open Food Facts term) |
| BR | gluten | Aveia, Flocos Grossos (7891000253403) | Aveia flocos grossos orgânica: Gluten source in Brazil; often cross-contaminated |
| BR | gluten | Aveia em flocos (7898994073048) | Aveia em flocos: Gluten source in Brazil; often cross-contaminated |
| BR | gluten | Bebida à Base De Aveia Barista Nude. Cai (7898994939719) | aveia: Gluten source in Brazil; often cross-contaminated |
| BR | gluten | Farinha de trigo tipo 1 (7897932900149) | Farinha de Trigo: allergens not verified (Open Food Facts term) |
| BR | lactose | Whey Chocolate (7896051166412) | LEITE SEMIDESNATADO E/OU LEITE SEMIDESNATADO RECONSTITUÍDO: allergens not verified (Open Food Facts term); CASEINATO DE CÁLCIO: allergens not verified (Open Foo |
| BR | gluten | Granola - Tia Sônia - 350g (7898115750292) | Flocos de aveia: allergens not verified (Open Food Facts term); gérmen de trigo: allergens not verified (Open Food Facts term) |
| BR | lactose | Leite desnatado (7896034610031) | Leite desnatado e estabilizantes: allergens not verified (Open Food Facts term); allergen statement: label declares: contains milk |
| BR | lactose | Sin Lactosa (7802930004188) | GRASA DE LECHE: allergens not verified (Open Food Facts term); PROTEÍNAS DE LECHE: allergens not verified (Open Food Facts term); allergen statement: label decl |
| BR | lactose | Leite Pó Instantâneo Integral Zero Lacto (7896048706126) | Leite integral: allergens not verified (Open Food Facts term) |
| BR | lactose | Iorgute Morango Natural Whey 14g Verde C (7898205924220) | Leite desnatado pasteurizado: allergens not verified (Open Food Facts term); concentrado proteico de soro de leite:  |
| BR | lactose | Yoghurt Batido Sabor Chirimoya Sin Azúca (7802920010670) | Leche descremada: allergens not verified (Open Food Facts term); leche en polvo descremada: allergens not verified (Open Food Facts term) |
| BR | lactose | Leite UHT Integral Parmalat 1 Litro (7896034610017) | Leite integral e estabilizantes: allergens not verified (Open Food Facts term); allergen statement: label declares: contains milk |
| BR | gluten | Arroz Sete Grãos+ (7896038300013) | aveia: Gluten source in Brazil; often cross-contaminated; cevada:  |
| BR | lactose | Achocolatado Itambé Zero Lactose (7896051128045) | Soro de leite elou soro de leite em pó reconstituído: allergens not verified (Open Food Facts term); leite integral elou leite em pó integral reconstituído: all |

</details>

## 7. Coverage: ingredients found in the database

| Market | Ingredients | Found | Coverage | Most frequent unknown items |
|---|---|---|---|---|
| BR | 19,102 | 17,752 | 92.9% | bacillus thuringiensis (31), streptomyces viridochromogenes (30), agrobacterium tumefaciens (28), poliglicerol polirricinoleato (21), minerais (20), a (19), e (19), zea mays (16), leudante quimico (14), l (12), acetato de dl alfa tocoferila (10), quot (10) |
| US | 24,330 | 23,001 | 94.5% | l (28), a b vitamin (22), processed with alkali (21), to preserve freshness (20), palmitate (16), to maintain freshness (14), for freshness (13), almondmilk (13), yellow 5 (12), mineral nutrients (10), yellow 6 (10), red 40 (10) |
| FR | 11,046 | 10,503 | 95.1% | e (17), b9 (16), bouillon (16), presence naturelle de polyphenols (16), d (14), origine : france (13), mineraux (10), mais (9), origine france (8), pp (7), origine: france (7), riboflavine (7) |
| DE | 11,365 | 10,424 | 91.7% | e (10), d (9), mais (9), emulgente (6), a (6), tricalciumphosphat (5), riboflavine (5), origine : france (5), c (4), secer (4), sol (4), tricalciumcitrat (4) |

## 8. Metamorphic tests (properties that must hold for any label)

| Property | Checks | Failures |
|---|---|---|
| STRICT is never milder | 22,586 | 0 |
| adding 'may contain milk' never improves a milk verdict | 5,993 | 0 |
| ingredient order does not change the verdict | 20,399 | 24 |
| same input, same verdict | 22,586 | 0 |
| upper case does not change the verdict | 22,586 | 0 |

Examples of failures, ingredient order does not change the verdict:
- 7891103221255 (lactose): Farinha de arroz, amido de milho, banana em flocos, vitaminas e minerais zinco), vitamina A (palmitato de retinila), vit
- 7802900228170 (lactose): Yoghurt (89%): Leche parcialmente descremada, crema de leche, azúcar, almidón de maíz modificado, sólidos lácteos, gelat
- 7802900228170 (gluten): Yoghurt (89%): Leche parcialmente descremada, crema de leche, azúcar, almidón de maíz modificado, sólidos lácteos, gelat
- 7802900228170 (vegan): Yoghurt (89%): Leche parcialmente descremada, crema de leche, azúcar, almidón de maíz modificado, sólidos lácteos, gelat
- 7896009301155 (lactose): Atum, óleo vegetal de soja, água, sal e extrato vegetal em pó (extratos de soja, cenoura e batata), Sem conservantes, Fo

## 9. Performance

167,314 engine runs: median 3.8 ms, 95th percentile 15.1 ms per label.
