# Standards, certifications and evidence (BR / US / EU) - v0.1

How a label check relates to the standards a food certification, testing and compliance company works under. Use it to say what a claim needs as evidence and who can provide it. Not legal advice.

Status (2026-10-17): items checked against the sources at the bottom. Items marked TO VERIFY need the official text before publishing a result.

## The core principle: screening is not certification
- **Certification** of a product or scheme (organic, non-GMO, GFSI food safety) is done by a certification body accredited to **ISO/IEC 17065** (for example by ANAB in the US, UKAS in the UK, INMETRO/Cgcre in Brazil, ACCREDIA in Italy, BELAC in Belgium). Management-system certification (ISO 22000) uses **ISO/IEC 17021-1**.
- **Thresholds** (GMO %, gluten ppm, lactose mg) can only be shown by a laboratory accredited to **ISO/IEC 17025**. In Brazil, labs serving Anvisa are also listed in REBLAS.
- So the agent never says a product *is* organic, non-GMO, gluten-free or compliant. It says what the label claims, whether the claim is consistent with the ingredients, and which evidence settles it: a certificate (body, number, scope, validity), a lab report, a supplier specification or statement.

## Evidence types to ask for
| Claim or question | Evidence that settles it | Who issues it |
|---|---|---|
| Organic | Certificate in the certifier's public register | Body accredited to ISO/IEC 17065 and recognised by the market's authority (MAPA, USDA NOP, EU control body) |
| Non-GMO / GMO content | Non-GMO certificate (Non-GMO Project, VLOG, ProTerra) or a PCR result | Certification body; ISO/IEC 17025 laboratory |
| Gluten-free (threshold) | Lab result (gluten below 20 ppm in the US and EU) | ISO/IEC 17025 laboratory |
| Lactose-free (BR threshold 100 mg/100 g) | Lab result | ISO/IEC 17025 laboratory |
| Allergen cross-contact | Supplier's allergen statement and risk assessment | Supplier (GFSI schemes require allergen management) |
| Vegan, halal, kosher | Certificate | Private certification schemes |

## GMO labelling by market
| Market | Rule | Threshold and wording |
|---|---|---|
| Brazil | Decreto 4.680/2003; Portaria MJ 2.658/2003 (symbol). The STJ confirmed the 1% limit in 2024 | Above 1% of the product: the consumer must be told; the label shows the "T" symbol (black T in a yellow triangle) on the main panel and wording such as "(produto) transgênico" or "contém (ingrediente) transgênico". A bill to remove the symbol (PLC 34/2015) was debated; check its status (TO VERIFY) |
| United States | National Bioengineered Food Disclosure Standard (7 CFR Part 66), USDA AMS | Foods on the List of Bioengineered Foods (for example corn, soybean, canola, cotton, sugar beet, alfalfa, some papaya, potato, squash, apple, eggplant, pineapple and sugarcane varieties, AquAdvantage salmon) are presumed bioengineered unless records show otherwise. Disclosure ("Bioengineered", "Derived from bioengineering", the BE symbol, a QR code or text message) is required unless inadvertent presence is 5% or less per ingredient. Highly refined ingredients with no detectable modified genetic material may be exempt |
| European Union | Regulation (EC) 1829/2003, Articles 12-13; traceability in Regulation (EC) 1830/2003 | "Genetically modified" or "produced from genetically modified (name)" unless GM material is 0.9% or less per ingredient and adventitious or technically unavoidable; the operator must show the steps taken to avoid it |

Private non-GMO standards are stricter than these laws (for example ProTerra sets a limit below 0.1% for adventitious EU-authorised GM material, with PCR testing at critical control points).

## Organic labelling by market
| Market | Rule | What the label needs |
|---|---|---|
| Brazil | Lei 10.831/2003; Decreto 6.323/2007; IN MAPA 18/2014 | The SisOrg seal, used only on certified organic products from units under control, plus the certifier's identification |
| United States | USDA National Organic Program, 7 CFR Part 205 | "100 percent organic" / "organic" / "made with organic" categories; the certifying agent named on the information panel ("Certified organic by …", 205.303(b)(2) and 205.304(b)(2), wording TO VERIFY in the eCFR) |
| European Union | Regulation (EU) 2018/848 | The EU organic logo, the code number of the control body or authority, and the place of farming ("EU Agriculture", "non-EU Agriculture", "EU/non-EU Agriculture") |

## Food safety schemes (GFSI) and what they expect from label checks
- GFSI-benchmarked schemes include BRCGS, SQF, FSSC 22000 and IFS. Certification bodies audit sites against them.
- BRCGS Food Safety (Issue 9) has fundamental requirements on **allergen management** and **labelling and pack control**: a procedure for artwork approval and sign-off, products labelled to meet the law of the country of use, and verification that claims (for example "gluten-free", "suitable for vegetarians") are supported. Exact clause wording TO VERIFY against the standard.
- ISO 22000 / HACCP principles that apply to this agent: **traceability** (each decision linked to the product, supplier, lot and artwork version), **document control** (every result names the rules and data version), and **records** (the audit log keeps each check and its basis).
- GFSI schemes also require a **food fraud vulnerability assessment**. Ingredients often named in fraud reports (for example olive oil, honey, spices, fish species, fruit juice; list TO VERIFY against the EU Agri-Food Fraud Network reports or a fraud database) deserve a supplier authenticity check; this is a pointer for the analyst, not a finding about a product.

## How the agent uses this
- In Analyst mode, report the tool's checklist rows "GMO labelling", "Non-GMO claim", "Organic claim" and "Other certification mark" with their basis, and ask for the evidence in the table above.
- When opening a review ticket, ask for the product name, supplier, lot or batch and artwork version (traceability).
- Transcribe seals and symbols as text in brackets so the rules can see them: "[seal: SisOrg]", "[symbol: T in yellow triangle]", "[seal: USDA Organic]", "[logo: EU organic, code BR-BIO-000]", "[seal: Non-GMO Project Verified]".

## Sources
- FoodChain ID accreditations (ISO/IEC 17065, 17025, 17020, 17021-1; USDA NOP; Non-GMO Project; INMETRO; REBLAS): https://www.foodchainid.com/accreditations/
- FoodChain ID certification services (GFSI, Non-GMO, organic): https://www.foodchainid.com/certification/
- FoodChain ID ANAB certificate (ISO/IEC 17065): https://www.foodchainid.com/wp-content/uploads/sites/24/2026/04/ANAB-Certificate-of-Accreditation-FoodChain-ID-Continued-Accreditation-ATFGIJAA.pdf
- FSSC 22000 certification body listing: https://www.fssc.com/trust/certification-bodies/foodchain-id-certification-s-a
- Non-GMO Project approved lab certificate (Brazil): https://www.foodchainid.com/wp-content/uploads/sites/24/2026/06/FY2026_NGP-Approved-Lab-Certificate-FoodChain-ID-Testing_Analises.pdf
- ProTerra standard (non-GMO limit and PCR testing): https://www.proterrafoundation.org/wp-content/uploads/2021/03/2021-03-02-PTF-Certification-Procedure.pdf
- Decreto 4.680/2003: https://www.contabeis.com.br/legislacao/23696/decreto-4680-2003/
- STJ on the 1% limit (2024): https://www.conjur.com.br/2024-out-16/transgenicos-so-devem-constar-no-rotulo-se-forem-1-do-produto-diz-stj/
- T symbol (Portaria 2.658/2003), IDEC: https://idec.org.br/em-acao/artigo/identificar-transgenico-da-ao-consumidor-poder-de-escolha
- USDA List of Bioengineered Foods: https://www.ams.usda.gov/rules-regulations/be/bioengineered-foods-list
- USDA BE list update (sugarcane, squash): https://www.hoganlovells.com/en/publications/usda-finalizes-updates-to-list-of-bioengineered-foods
- BE 5% threshold and presumption: https://www.foodonline.com/doc/usda-s-bioengineered-food-disclosure-rule-what-manufacturers-need-to-know-0001
- Regulation (EC) 1829/2003, Article 12: https://www.legislation.gov.uk/eur/2003/1829/article/12
- 7 CFR 205.303: https://www.ecfr.gov/current/title-7/subtitle-B/chapter-I/subchapter-M/part-205/subpart-D/section-205.303
- IN MAPA 18/2014 (SisOrg seal): https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/organicos/arquivos-organicos/IN_18_de_20062014_SELO_BRASILEIRO.pdf
- EU organic labelling (Regulation 2018/848), GS1 guideline: https://gs1.eu/wp-content/uploads/2023/09/GS1-in-EU-Organic-Products-Guideline-v1.1.pdf
- BRCGS Issue 9 product control summary: https://ascfoodsafety.com/brcgs-for-food-safety-changes-product-control/
