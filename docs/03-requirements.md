# 03 - Requirements

## Scope (v0.1, primary use case updated in v0.4, scope statement in v0.6)
Since v0.4 the primary use case is the Analyst workflow: label compliance first pass for BR, US and EU (decision D-07, [05 · Analyst workflow](05-analyst-workflow.md)). Shopper and Cook stay as secondary modes.

**In:** what the label text shows (ingredient lists from photos, typed text and recipes; allergen, gluten and lactose statements; claims and seals), checked against its own statements and the market's rules, as a first pass that a named person signs; allergen and intolerance flags; animal versus plant origin; vegan and vegetarian checks; human-review handoff with traceability.

**Out:** certifying anything (only ISO/IEC 17065 bodies certify); deciding the origin of an ambiguous ingredient (flavourings, enzymes, emulsifiers, processing aids) without a supplier declaration; anything not printed on the pack (cross-contact controls, recipes behind a brand); medical advice; legal or regulatory rulings; live data connections; user accounts; barcode lookup; nutrition analysis; halal and kosher. For each out-of-scope point the agent says which evidence would settle it.

## User stories
Priority: P1 = needed for the demo, P2 = next. US-15 moved to P1 and US-18 was added when the Analyst workflow became primary (v0.4); US-21 to US-24 answer the external review of v0.5 (v0.6).

| ID | Priority | Story | Acceptance criteria |
|---|---|---|---|
| US-01 | P1 | As a shopper, I want to photograph a label and get a short verdict, so I can decide in the aisle. | The transcription is shown. The verdict is one icon plus one sentence (15 words or fewer). A next step is given. |
| US-02 | P1 | As a person with low literacy, I want simple words. | Average sentence 20 words or fewer, and at most 10% over 25 words. Each technical term explained in a few words. The agent offers a simpler explanation once. An LLM judge with a fixed rubric scores plain language 4/5 or higher. |
| US-03 | P1 | As a person with lactose intolerance, I do not want false alarms. | Cocoa butter, lactic acid and coconut milk are not flagged. Butter and aged cheese are 🟡 with a note that tolerance varies. |
| US-04 | P1 | As a person with celiac disease or an allergy, I need strict handling. | Unclear items and may-contain warnings are 🔴. The agent recommends confirming with the manufacturer and never reassures. |
| US-05 | P1 | As a user, I want to be told when the photo is not good enough. | The agent asks for a retake and lists what is missing. No verdict from a partial reading. |
| US-06 | P1 | As a user, I want contradictions on the label pointed out. | Mismatches are reported politely, for example malt listed with "não contém glúten", milk missing from the allergen statement, or "zero lactose" with whey listed. |
| US-07 | P1 | As a user, I never want the agent to say a product is safe. | Wording is "I did not find X in the text I could read". Zero violations in an adversarial test set, including users who insist on a yes or no, in Portuguese and English. The tool returns the safe wording with every verdict. |
| US-08 | P1 | As a user with symptoms now, I want help, not analysis. | The agent tells me to seek emergency help with the local number (SAMU 192, 911, 112) and does not analyse the label. The tool also returns "urgent" when symptoms are described. No false emergency on a past reaction or on real labels. |
| US-09 | P1 | As a user, I want answers in my language. | The agent replies in the language I write in (Portuguese or English) and transcribes labels in their original language. |
| US-10 | P1 | As a cook, I want a table with the origin and fit of each ingredient for a diet. | Each ingredient has an origin class and a fit (🔴, 🟡, 🟢). A summary line is given per diet. |
| US-11 | P1 | As a cook, I want unclear ingredients flagged, not guessed. | Oils, fats or shortening with no stated source, emulsifiers, glycerin, natural flavors and enzymes are "Can be either" and never assumed plant-based. |
| US-12 | P1 | As a cook, I want to know what to ask the supplier. | Each 🟡 comes with a concrete check: a product label, a supplier statement or a certificate. |
| US-13 | P1 | As a cook with allergic guests, I need a strict reminder. | The agent says the check must not be the only safeguard. |
| US-14 | P2 | As a cook, I want substitutes for ingredients that do not fit. | Substitutes only for 🔴 items, as generic types, and re-checked against the same profile (for example plant butters may contain soy or tree nuts). |
| US-15 | P1 | As an analyst, I want a consistency check and a handoff note. | The agent lists declared allergens for the market on the label, mismatches, "Escalate to human review: Yes/No" and a 3-line note. |
| US-16 | P2 | As the product owner, I want to track quality over time. | Every test run is logged against the golden set; pass rates for v0.1 and v0.2 are compared. |
| US-17 | P2 | As the product owner, I want ingredient data from public sources with clear provenance, so coverage grows without new risk. | Every database row names its source. Imported data never turns a missing allergen fact into 🟢. Licenses are credited. Coverage is measured on labels not used for tuning. |
| US-18 | P1 | As an analyst, I want each market rule checked with its legal basis, so I know what passed, what failed and what I must look at myself. | A checklist per market (BR, US, EU) with pass / fail / review / n/a and the regulation for each check. Points text cannot settle (format, amounts, emphasis) are always "review", never "pass". |
| US-19 | P1 | As an analyst, I want claims that depend on a certificate or a lab test (organic, non-GMO, GMO labelling, certification marks) checked against the market's rule, so I know which evidence to collect. | GMO labelling per market (BR 1% with the T symbol, US bioengineered disclosure, EU 0.9%), organic particulars per market (SisOrg; certifier statement; EU code number), and certification marks are listed with their basis. The agent never states that a product is certified, organic, non-GMO or compliant; it names the evidence (certificate, ISO/IEC 17025 lab report, supplier record). |
| US-20 | P1 | As an analyst, I want a clear decision for each label. | One of: Ready for sign-off (all checks pass or do not apply; a named reviewer still signs), Request evidence (claims or thresholds that need a certificate, lab report or supplier record) or Escalate (a failed check or a contradiction, including an organic claim with a declared GMO). The tool never approves a label. |
| US-21 | P1 | As an analyst, I want the agent to stop when it cannot read the label reliably, so a misread never becomes a pass. | The agent declares how well it read the label (`transcription_confidence`, `source`, `complete_pack`). Low confidence or no ingredient list: no verdict and no check (`needs_manual_review`), and the agent asks for a clearer photo of the whole pack. A word marked [?] or medium confidence: no item and no verdict is 🟢, no check passes. A photo of part of the pack: a missing statement is review, not fail. |
| US-22 | P1 | As a compliance lead, I want every label decision signed by a named reviewer, with a reason for every override, so the audit trail stands up. | `record_review_decision` needs the `check_id` and the reviewer's name; a rejection or an override needs a reason; approving a label the tool did not mark ready is recorded as an override. The audit log links each decision to the input hash, the rules version and the data version. `usage_stats` reports the override rate. |
| US-23 | P1 | As a compliance lead, I want each rule's legal basis, the date it applies from, how well it was checked and its history in one register, so I know what the engine applies and when it must be reviewed again. | Every checklist row and mismatch carries `rule_id` and its citation from the register. A basis not yet verified never gives pass or fail. CI fails when a review is overdue, a rule has no test or the register and engine versions differ. |
| US-24 | P2 | As the product owner, I want every benchmark miss explained by its cause, so I know what to fix and what the number means. | Each miss is assigned to ingestion, parsing, taxonomy or reference definition with keyword lists independent of the engine. Extraction rates are reported by input type, with unmeasured types stated. A second reference (the manufacturer's statement) is checked from the ingredients alone. |

## Non-functional requirements
- **Safety:** no diagnosis, no medication or dose advice, no claims of safety or "vegan for sure".
- **Honesty:** labels cannot show processing aids or cross-contact; the agent says so in diet checks. "Vegan" claims are treated as supporting evidence, not proof.
- **Privacy:** no personal data; screenshots are cropped; only public or invented examples.
- **Accessibility:** icons always paired with words; short sentences; text-only output.
- **Transparency:** the agent shows what it read and how confident it is.
- **Maintainability:** instructions and knowledge files are versioned, with a changelog.
- **Data provenance:** curated data wins over imported data; imports are scripted, versioned and credited (Open Food Facts under the ODbL).
- **Fail closed:** when the input may be wrong (unsure reading, part of the pack, no list), the result is review or no verdict, never pass or 🟢.
- **Traceability:** every result can be reproduced from its `check_id`: the input hash, the parameters, the rules version and the data hash.
- **Change control:** a rule changes only with a test, a register entry, a changelog line and a new rules version; a data change that makes a term milder needs a second reviewer.
- **Cost:** zero.

## Definition of done for v0.1
- All P1 stories pass in the golden set, with results recorded.
- One user acceptance test with a real user.
- Documentation complete and consistent with the agent.
- Screen recording of the demo (one case per mode).

## Open questions (if this became a real project)
- Where would ingredient-origin data come from, and who approves it? (v0.3 uses curated glossaries plus Open Food Facts; production would need supplier specifications.)
- Which diets need certification-level evidence (halal, kosher)?
- How would answers be logged and reviewed, and what is the human-review turnaround?
- What data-privacy rules apply to customer-facing use?
