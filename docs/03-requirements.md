# 03 - Requirements

## Scope (v0.1)
**In:** ingredient lists from label photos, typed text and recipes; allergen and intolerance flags; animal versus plant origin; vegan and vegetarian checks; cross-check against label statements; human-review handoff.

**Out:** medical advice; legal or regulatory rulings; live data connections; user accounts; barcode lookup; nutrition analysis; halal and kosher (they need certification-level evidence).

## User stories
Priority: P1 = needed for the demo, P2 = next.

| ID | Priority | Story | Acceptance criteria |
|---|---|---|---|
| US-01 | P1 | As a shopper, I want to photograph a label and get a short verdict, so I can decide in the aisle. | The transcription is shown. The verdict is one icon plus one sentence (15 words or fewer). A next step is given. |
| US-02 | P1 | As a person with low literacy, I want simple words. | Short sentences. Each technical term explained in one line. The agent offers a simpler explanation once. |
| US-03 | P1 | As a person with lactose intolerance, I do not want false alarms. | Cocoa butter, lactic acid and coconut milk are not flagged. Butter and aged cheese are 🟡 with a note that tolerance varies. |
| US-04 | P1 | As a person with celiac disease or an allergy, I need strict handling. | Unclear items and may-contain warnings are 🔴. The agent recommends confirming with the manufacturer and never reassures. |
| US-05 | P1 | As a user, I want to be told when the photo is not good enough. | The agent asks for a retake and lists what is missing. No verdict from a partial reading. |
| US-06 | P1 | As a user, I want contradictions on the label pointed out. | Mismatches are reported politely, for example malt listed with "não contém glúten", milk missing from the allergen statement, or "zero lactose" with whey listed. |
| US-07 | P1 | As a user, I never want the agent to say a product is safe. | Wording is "I did not find X in the text I could read". Zero violations in tests. |
| US-08 | P1 | As a user with symptoms now, I want help, not analysis. | The agent tells me to seek medical help and stops analysing. |
| US-09 | P1 | As a user, I want answers in my language. | The agent replies in the language I write in (Portuguese or English) and transcribes labels in their original language. |
| US-10 | P1 | As a cook, I want a table with the origin and fit of each ingredient for a diet. | Each ingredient has an origin class and a fit (🔴, 🟡, 🟢). A summary line is given per diet. |
| US-11 | P1 | As a cook, I want unclear ingredients flagged, not guessed. | Oils, fats or shortening with no stated source, emulsifiers, glycerin, natural flavors and enzymes are "Can be either" and never assumed plant-based. |
| US-12 | P1 | As a cook, I want to know what to ask the supplier. | Each 🟡 comes with a concrete check: a product label, a supplier statement or a certificate. |
| US-13 | P1 | As a cook with allergic guests, I need a strict reminder. | The agent says the check must not be the only safeguard. |
| US-14 | P2 | As a cook, I want substitutes for ingredients that do not fit. | Substitutes only for 🔴 items, as generic types, and re-checked against the same profile (for example plant butters may contain soy or tree nuts). |
| US-15 | P2 | As an analyst, I want a consistency check and a handoff note. | The agent lists declared allergens for the market on the label, mismatches, "Escalate to human review: Yes/No" and a 3-line note. |
| US-16 | P2 | As the product owner, I want to track quality over time. | Every test run is logged against the golden set; pass rates for v0.1 and v0.2 are compared. |

## Non-functional requirements
- **Safety:** no diagnosis, no medication or dose advice, no claims of safety or "vegan for sure".
- **Honesty:** labels cannot show processing aids or cross-contact; the agent says so in diet checks. "Vegan" claims are treated as supporting evidence, not proof.
- **Privacy:** no personal data; screenshots are cropped; only public or invented examples.
- **Accessibility:** icons always paired with words; short sentences; text-only output.
- **Transparency:** the agent shows what it read and how confident it is.
- **Maintainability:** instructions and knowledge files are versioned, with a changelog.
- **Cost:** zero.

## Definition of done for v0.1
- All P1 stories pass in the golden set, with results recorded.
- One user acceptance test with a real user.
- Documentation complete and consistent with the agent.
- Screen recording of the demo (one case per mode).

## Open questions (if this became a real project)
- Where would ingredient-origin data come from, and who approves it?
- Which diets need certification-level evidence (halal, kosher)?
- How would answers be logged and reviewed, and what is the human-review turnaround?
- What data-privacy rules apply to customer-facing use?
