# Rules engine benchmark on real products (rules 0.4.0)

6000 products from Open Food Facts (most scanned per market, ingredient list in the label language), 160,570 engine runs, data 644 curated + 35051 Open Food Facts terms. Sample: `tests/benchmark/off-products.jsonl` (ODbL). Reproduce: `uv run --directory mcp-server python ../tests/benchmark/run_benchmark.py`.

**How to read it.** Reference allergens are what Open Food Facts records for each product. They come from manufacturers and from Open Food Facts' own parsing, which uses the same taxonomy this project imports, so agreement is an upper bound. Labels (vegan, gluten-free, lactose-free) are claims printed on the pack. The ingredient text alone is checked: a separate allergen box that was not transcribed into the ingredient field is invisible to the engine.

## 1. Safety: declared allergens the engine missed (false greens)

| Market | Allergen | Products | 🔴 | 🟡 | 🟢 missed | Miss rate | Miss rate in STRICT |
|---|---|---|---|---|---|---|---|
| BR | celery | 9 | 8 | 1 | 0 | 0.0% | 0.0% |
| BR | crustacean | 1 | 0 | 1 | 0 | 0.0% | 0.0% |
| BR | egg | 39 | 36 | 3 | 0 | 0.0% | 0.0% |
| BR | fish | 11 | 10 | 1 | 0 | 0.0% | 0.0% |
| BR | gluten | 218 | 193 | 24 | 1 | 0.5% | 0.5% |
| BR | milk | 165 | 161 | 4 | 0 | 0.0% | 0.0% |
| BR | mollusc | 1 | 0 | 1 | 0 | 0.0% | 0.0% |
| BR | mustard | 5 | 4 | 1 | 0 | 0.0% | 0.0% |
| BR | peanut | 39 | 37 | 2 | 0 | 0.0% | 0.0% |
| BR | sesame | 1 | 1 | 0 | 0 | 0.0% | 0.0% |
| BR | soy | 225 | 178 | 46 | 1 | 0.4% | 0.4% |
| BR | sulphites | 13 | 1 | 12 | 0 | 0.0% | 0.0% |
| BR | tree_nuts | 35 | 27 | 8 | 0 | 0.0% | 0.0% |
| DE | celery | 19 | 16 | 3 | 0 | 0.0% | 0.0% |
| DE | crustacean | 3 | 2 | 0 | 1 | 33.3% | 33.3% |
| DE | egg | 72 | 57 | 13 | 2 | 2.8% | 2.8% |
| DE | fish | 25 | 21 | 3 | 1 | 4.0% | 4.0% |
| DE | gluten | 289 | 263 | 26 | 0 | 0.0% | 0.0% |
| DE | lupin | 3 | 2 | 1 | 0 | 0.0% | 0.0% |
| DE | milk | 320 | 293 | 23 | 4 | 1.2% | 1.2% |
| DE | mustard | 31 | 30 | 1 | 0 | 0.0% | 0.0% |
| DE | peanut | 35 | 22 | 13 | 0 | 0.0% | 0.0% |
| DE | sesame | 16 | 6 | 9 | 1 | 6.2% | 6.2% |
| DE | soy | 194 | 175 | 19 | 0 | 0.0% | 0.0% |
| DE | sulphites | 28 | 26 | 2 | 0 | 0.0% | 0.0% |
| DE | tree_nuts | 132 | 119 | 13 | 0 | 0.0% | 0.0% |
| FR | celery | 42 | 33 | 9 | 0 | 0.0% | 0.0% |
| FR | crustacean | 3 | 3 | 0 | 0 | 0.0% | 0.0% |
| FR | egg | 86 | 75 | 11 | 0 | 0.0% | 0.0% |
| FR | fish | 21 | 21 | 0 | 0 | 0.0% | 0.0% |
| FR | gluten | 408 | 391 | 16 | 1 | 0.2% | 0.2% |
| FR | lupin | 4 | 0 | 4 | 0 | 0.0% | 0.0% |
| FR | milk | 316 | 284 | 27 | 5 | 1.6% | 1.6% |
| FR | mustard | 22 | 18 | 4 | 0 | 0.0% | 0.0% |
| FR | peanut | 36 | 32 | 4 | 0 | 0.0% | 0.0% |
| FR | sesame | 21 | 15 | 6 | 0 | 0.0% | 0.0% |
| FR | soy | 181 | 159 | 22 | 0 | 0.0% | 0.0% |
| FR | sulphites | 17 | 15 | 2 | 0 | 0.0% | 0.0% |
| FR | tree_nuts | 120 | 101 | 18 | 1 | 0.8% | 0.8% |
| US | celery | 37 | 32 | 5 | 0 | 0.0% | 0.0% |
| US | egg | 67 | 58 | 8 | 1 | 1.5% | 1.5% |
| US | fish | 15 | 14 | 1 | 0 | 0.0% | 0.0% |
| US | gluten | 346 | 316 | 28 | 2 | 0.6% | 0.6% |
| US | milk | 326 | 304 | 18 | 4 | 1.2% | 1.2% |
| US | mollusc | 6 | 4 | 2 | 0 | 0.0% | 0.0% |
| US | mustard | 20 | 17 | 3 | 0 | 0.0% | 0.0% |
| US | peanut | 103 | 93 | 10 | 0 | 0.0% | 0.0% |
| US | sesame | 37 | 31 | 6 | 0 | 0.0% | 0.0% |
| US | soy | 261 | 220 | 41 | 0 | 0.0% | 0.0% |
| US | sulphites | 15 | 13 | 2 | 0 | 0.0% | 0.0% |
| US | tree_nuts | 168 | 153 | 15 | 0 | 0.0% | 0.0% |
| **All** | | **4607** | 4090 | 492 | **25** | **0.5%** | **0.5%** |

### Missed allergens (first 40)

| Market | Allergen | Product | Ingredient text (start) |
|---|---|---|---|
| BR | soy | Biscoito Aveia e Mel (7891000913000) | @Marca Registrada do Société des Produits Nestlé SX • reccde gordura de 7% para 6%, gordura saturada do alimentaralteradod06% para e do s6diode20/o referência.  |
| BR | gluten | Paçoquita 3,84 GR. (7896336006631) | roasted and crushed peanut, sugar and salt. ATTENTION ALLERGIC PEOPLE: IT CONTAINS PEANUT. GLUTEN FREE. Product exempted from sanitary registration as per ANVIS |
| US | milk | great grains raisins, dates & pecans cer (0884912126115) | Whole Grain Wheat, Raisins, Cane Sugar, Whole Grain Rolled Oats, Dates, Wheat Flour, Malted Barley Flour, Rice Flour, Pecans, Expeller Pressed Canola Oil, Salt, |
| US | milk | Light Rye Crispbread Swedish Style (0033617322616) | WHOLE GRAIN RYE FLOUR, SALT. |
| US | gluten | Organic Garbanzo Beans (00502610) | ORGANIC GARBANZO BEANS, WATER, SEA SALT. |
| US | milk | Organic Garbanzo Beans (00502610) | ORGANIC GARBANZO BEANS, WATER, SEA SALT. |
| US | milk | Organic Popcorn with Organic Extra Virgi (00921138) | ORGANIC POPCORN, ORGANIC EXTRA VIRGIN OLIVE OIL, SEA SALT |
| US | gluten | Tortilla Wraps (0027331032128) | Soybean, water, salt, caramel color, star anise, calcium sulfate |
| US | egg | Omega-3 Trail Mix (0078742221427) | DRIED SWEETENED CRANBERRIES (CRANBERRIES, SUGAR, SUNFLOWER OIL), WALNUTS, PEPITAS, ALMONDS, PECANS, VEGETABLE OIL PEANUT OIL, COTTONSEED OIL, SOYBEAN OIL AND/OR |
| FR | milk | Cacao céréales (3175681261372) | Farine de blé 54,9%, huile de colza, sucre non raffiné, germe de blé 5,6%, cacao maigre en poudre¹ 5,1%, amidon de blé, fibre de blé, farine de riz 3,1%, fèves  |
| FR | gluten | Chicoree soluble nature bio 100g (3067140037898) | Chicorée Soluble |
| FR | milk | Les Fourrées  -  Beurre de Cacahuète & C (3770008009882) | Céréales* 51% (farinė de riz complet*, farine de maïs*), beurre de cacahuète* 31%, sucre .de betterave*, cacao en poudre* 6,5%, une pointe de sel. |
| FR | milk | Tartines Craquantes Multi-Céréales (3175681037885) | Farine de riz* 67,7g, farine de sarrasin* 29,7g), farine de quinoa* 9,5g, sucre de canne roux, sel de mer. |
| FR | tree_nuts | Natural Coconut Cream (8886303210207) | Natural Coconut Cream (99.9%), Xanthan Gum, Guar Gum, Carrageenan. |
| FR | milk | Saveir Sel & Vinaigre (3497911105127) | Pommes de terre (62,9%), huile de tournesol (31%), farine de blé, correcteur d'acidité : diacétate de sodium, sel, sucre, acidifiants: (acide citrique, acide ma |
| FR | milk | Biscuits Petit déj Bio Céréales Miel (3175681272934) | Flocons d'avoine* 33%, farine complète de grand épeautre (blé)* 18,1%, farine complète de blé* de meule 16,2% huile de tournesol oléique*, sucre de canne*, riz* |
| DE | sesame | Reiswaffeln (20884680) | table salt (0.31%), rice (99.69%) |
| DE | egg | Cornichons Gurken (20004361) | Gurken, Wasser, Branntweinessig, Zucker, Speisesalz, Gewürze (enthält Senf), Zwiebeln, Paprika rot, Gewürzextrakt |
| DE | milk | Cornichons Gurken (20004361) | Gurken, Wasser, Branntweinessig, Zucker, Speisesalz, Gewürze (enthält Senf), Zwiebeln, Paprika rot, Gewürzextrakt |
| DE | milk | Fette croccanti con sesamo (20006167) | Farina di segale integrale (84%), sesamo (10%), sale |
| DE | egg | Pan Bauletto Bianco (8076809504720) | Farina Di Grano Tenero Tipo 0 71,7%, Acqua, Olio Extravergine Di Oliva 2,4%, Lievito, Sale, Farina D'orzo Maltato, |
| DE | milk | Pan Bauletto Bianco (8076809504720) | Farina Di Grano Tenero Tipo 0 71,7%, Acqua, Olio Extravergine Di Oliva 2,4%, Lievito, Sale, Farina D'orzo Maltato, |
| DE | milk | RUMMO Mezzi Rigatoni No 51 (8008343200516) | Semoule de blé dur de qualité supérieure. |
| DE | crustacean |  (4056489152903) | 58% chou chinois, eau, 2,5% carotte, 2% radis, 2% radis vert, 1,8% sel, 1,5% sucre, 0,5% oignon, 0,5% oignon de printemps, 0,5% ail, 0.3% piment rouge en poudre |
| DE | fish |  (4056489152903) | 58% chou chinois, eau, 2,5% carotte, 2% radis, 2% radis vert, 1,8% sel, 1,5% sucre, 0,5% oignon, 0,5% oignon de printemps, 0,5% ail, 0.3% piment rouge en poudre |

## 2. Claims on the pack vs the engine

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
| FR | vegan | 127 | 26 | 93 | 8 |
| US | gluten | 626 | 43 | 559 | 24 |
| US | lactose | 64 | 10 | 18 | 36 |
| US | vegan | 290 | 103 | 178 | 9 |

### Conflicts (first 30)

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

## 3. Coverage: ingredients found in the database

| Market | Ingredients | Found | Coverage | Most frequent unknown items |
|---|---|---|---|---|
| BR | 18642 | 17352 | 93.1% | bacillus thuringiensis (28), streptomyces viridochromogenes (27), agrobacterium tumefaciens (27), poliglicerol polirricinoleato (21), a (19), e (19), minerais (18), leudante quimico (14), zea mays (14), l (10), acetato de dl alfa tocoferila (9), quot (9) |
| US | 23558 | 22292 | 94.6% | l (28), a b vitamin (22), processed with alkali (21), to preserve freshness (18), palmitate (16), to maintain freshness (14), for freshness (13), almondmilk (13), yellow 5 (12), mineral nutrients (10), acidophilus (9), yellow 6 (9) |
| FR | 10566 | 10034 | 95.0% | e (17), b9 (16), bouillon (16), presence naturelle de polyphenols (16), d (14), origine : france (13), mineraux (10), origine france (8), mais (8), pp (7), origine: france (7), riboflavine (7) |
| DE | 10682 | 9774 | 91.5% | e (10), d (9), mais (8), a (6), riboflavine (5), origine : france (5), c (4), secer (4), sol (4), emulgente (4), tricalciumcitrat (4), kartoffelpureepulver (4) |

## 4. Metamorphic tests (properties that must hold for any label)

| Property | Checks | Failures |
|---|---|---|
| STRICT is never milder | 22,586 | 0 |
| adding 'may contain milk' never improves a milk verdict | 5,993 | 0 |
| ingredient order does not change the verdict | 20,346 | 45 |
| same input, same verdict | 22,586 | 0 |
| upper case does not change the verdict | 22,586 | 0 |

Examples of failures, ingredient order does not change the verdict:
- 7802900228170 (gluten): Yoghurt (89%): Leche parcialmente descremada, crema de leche, azúcar, almidón de maíz modificado, sólidos lácteos, gelat
- 7896009301155 (lactose): Atum, óleo vegetal de soja, água, sal e extrato vegetal em pó (extratos de soja, cenoura e batata), Sem conservantes, Fo
- 7898059340405 (lactose): Farinha de trigo enriquecida com ferro e ácido fólico, farinha de trigo integral, açúcar, sal refinado, amido de milho, 
- 6299871202611 (lactose): Folhas de Carqueja (Baccharis genistelloides, (Lamarck) Person), capítulos florais da Camomila (Matriarcaria recutita, L
- 6299871202611 (gluten): Folhas de Carqueja (Baccharis genistelloides, (Lamarck) Person), capítulos florais da Camomila (Matriarcaria recutita, L

## 5. Performance

160,570 engine runs: median 3.1 ms, 95th percentile 13.7 ms per label.
