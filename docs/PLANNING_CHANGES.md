# Planning changes

## More representative fictional paperwork

**Author:** Luke Hermon

I wanted the fictional test paperwork to look more realistic and better represent the documents ParentVault AI will need to handle. I expanded the test plan beyond a short scheduling paragraph to include formal multipart paperwork.

### Previous approach

I started with a short fictional recurring-schedule paragraph to isolate PDF extraction, model output, validation, and calendar arithmetic. I then wanted a stronger test of locating the operative schedule within a longer packet containing unrelated administrative material.

### Revised approach

I expanded the plan to include invented multipart documents with a cover, numbered provisions, settlement-style administrative material, a parenting-plan section, review instructions, and unsigned acknowledgment blocks. I kept a clear fictional label on every page so the test material cannot reasonably be mistaken for a filed document.

| Fixture | Purpose | Expected behavior |
|---|---|---|
| `formal_recurring_plan.pdf` | Longer text-based packet with a supported recurring rule | Extract the operative schedule; require review |
| `formal_plan_with_exceptions.pdf` | Regular rule plus holiday precedence and missing school-break dates | Flag unresolved provisions; do not approve a complete recurring-only calendar |
| `formal_recurring_plan_scanned.pdf` | Image-only version of the invented supported packet | Reject with an OCR-related explanation under current scope |

I used invented wording, identifiers, and scenarios. I kept private reference material out of the repository. I included the generator so I can reproduce the fixtures and an independently authored scenario answer file so I can compare outputs with expected results.

### Scope effect

I increased the realism of the test paperwork without claiming new OCR or comprehensive holiday capabilities. I am treating scanned inputs as an explicit boundary in this version. If I add OCR later, I will need a separate scope decision and checks for recognition errors. My current priority is to demonstrate supported inputs and make unsupported cases clear.

### Evidence still needed

The longer-fixture evaluation and a six-case held-out run are now recorded in EXPANDED_EVALUATION.md. I still need fresh untouched cases after the observed failures informed validation changes. Success on one short example does not establish that longer documents are handled reliably.

## Desktop workflow advancement

My R&D app now includes rule review, approval invalidation, month generation, SQLite save/reload, and CSV export. I wanted detailed code comments so I could understand how those parts connect and explain them during the walkthrough. The automated checks recorded a complete live pipeline pass on the initial fictional case. I distinguish that evidence from the Qt smoke check and backend tests. See EXPANDED_EVALUATION.md and ITERATION1_INCREMENT.md.
