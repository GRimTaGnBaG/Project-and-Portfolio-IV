# Running ParentVault

Double-click **Start ParentVault.cmd**. On the configured development computer, the launcher uses the installed ParentVault Python environment. On another Windows computer, install Python 3.12 and run **Setup ParentVault.cmd** once (internet required for dependencies), then use Start. LM Studio and its models are separate installations.

## First calendar

1. Click **Open sample plan** on Document. The included five-page PDF is fictional.
2. Click **Baseline extraction**. This path works without a model server.
3. Compare the proposed rules and page quotations with the source. The sample starts November 2, 2026, with seven A overnights followed by seven B overnights.
4. Check the review acknowledgment and select **Approve reviewed rules**.
5. Open Calendar and click **Generate approved month**. November has 30 rows; November 1 belongs to B, November 2–8 to A, and November 9–15 to B.
6. Export CSV, or open Saved Records, enter a plan name, and save. Loading a record requires fresh review and approval. The original PDF is not embedded in the database; extracted pages and source provenance are retained.

## Local model

Open LM Studio. Load an installed model and start the local server on port **1235**. Click **Check local model connection** in ParentVault. The research model alias is **parentvault-research**; another model can be selected by entering its exact identifier. Click **Local model extraction**, review its proposal, and approve only after checking the source. An unreachable server or invalid response remains a visible error. Baseline extraction is a separate method.

## Research comparison

Select a document, then open Research Comparison and run both methods. The window stays responsive while the model runs. If current rules were approved, their values are used as a labeled reviewed reference; this is not independent ground truth. Without approval, accuracy is unscored. Each method's output, error and elapsed time are shown. Export saves the summarized comparison; opening older results displays historical evidence. A comparison never changes approval.

## Files and data

Saved plans and the latest summarized comparison live in `%LOCALAPPDATA%\ParentVault`. CSV export lets the user choose a destination. `PARENTVAULT_DATA_DIR` overrides the data location for isolated verification. Updating or replacing application source does not remove these records. Earlier development databases remain in their original folders and are not automatically migrated or deleted.

Interactive extraction keeps raw model request/response content in memory. Explicit command-line research runners can create evidence archives. These archives and local databases are excluded from Git. A comparison summary can still contain extracted quotations; keep exports local unless sharing is intended.

## Supported MVP

The app handles text-based PDFs up to 10 MB, 30 pages and 40,000 extracted characters. Rules must describe a repeating 14-day A/B overnight cycle with an explicit anchor and matching source evidence. Calendar arithmetic is deterministic. Rule edits invalidate approval and previous dates. The baseline recognizes a narrow explicit alternating-week sentence; a model can propose additional 14-day patterns, subject to validation and review.

Scanned or encrypted PDFs, OCR, holiday overrides, incomplete schedules and comprehensive court-order interpretation are outside this version. Unsupported provisions block approval. Overnight ownership is not a precise handoff instruction. These are functional scope boundaries, not a promise that every parenting plan can be interpreted correctly.

## Troubleshooting

- **Window does not open:** run Setup once, or launch `python app.py` from the configured environment to see errors.
- **Model unavailable:** start LM Studio's server on 1235 and check its model identifier. The baseline remains available.
- **Approve disabled:** extract rules and check the review acknowledgment. Warnings and invalid evidence require resolution before approval.
- **Empty calendar:** approve current rules and click Generate for the displayed month. Changing month clears the prior export until generation runs again.
- **Close delayed:** an active inference request must finish or reach its timeout before the window closes safely.

## Verification

The November 4 desktop completion checkpoint passes 38 automated tests. A separate real local-model check exercises the fictional PDF, Qt inference worker, approval, 30 calendar rows, CSV, SQLite, fresh measured comparison, and mandatory review on reload. This is a bounded MVP, with the unsupported cases above retained explicitly.
