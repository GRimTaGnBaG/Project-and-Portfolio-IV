# Project and Portfolio IV

## ParentVault AI

I am developing a Windows desktop research application for turning supported text-based parenting-plan PDFs into reviewed recurring overnight calendars.

## Repository organization

The initial staged imports are complete. I keep a separate local development checkout and integrate reviewed changes into the publishing checkout. Original development commits retain their timestamps; integration and push dates are not claims that earlier work was newly written on those dates.

## Planned workflow

Select a fictional PDF, inspect extracted text and proposed rules, review the source evidence, approve the current rules, and generate an overnight calendar. Local storage and CSV export support checking the results.

## Scope

Use fictional research documents. The current input scope is text-based PDFs; scanned inputs require OCR that is not implemented. Model output and matching quotations still require human review. This application does not provide legal advice.

## Setup

Python 3.12 is the development target. The first staged import includes extraction, validation, a baseline experiment, and backend tests. From this repository folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run_research.py
```

The second staged import includes the desktop interface, approval workflow, SQLite storage, CSV export, and historical comparison view. Launch it with `.\.venv\Scripts\python.exe app.py`. The extractor also rejects mixed packets containing image-only pages so a readable cover cannot hide a scanned schedule.

A separate export safeguard validates the entire row batch before opening a destination, preventing malformed or duplicate rows from truncating an existing CSV. The final staged import includes longer fictional fixtures, evaluation runners, and expanded GUI checks. Experiment manifests are validated before inference to reject unsafe or duplicate case IDs and malformed answer keys. Thirty-five automated checks pass in the current desktop checkpoint.

## Desktop interface

The app has five sidebar pages: Document, Review Rules, Calendar, Saved Records, and Research Comparison. It includes native PDF viewing, editable rule fields, explicit approval acknowledgment, parent-labeled calendar cells, and saved-record search. The November 2 update also fixes filtered-record selection so Load/Delete cannot target an invisible previous selection. See [desktop design checkpoint](docs/DESKTOP_DESIGN.md).

## Research and verification

```powershell
.\.venv\Scripts\python.exe evaluate_dataset.py --split held_out --model "YOUR_LOADED_MODEL_IDENTIFIER"
```

Live inference requires the local LM Studio server at `http://127.0.0.1:1235/v1` and the specified loaded model. The development alias is `parentvault-research`. No model download is performed by these scripts. Rerunning a case does not make it an untouched held-out example; preserve the documented limits when interpreting results.

The comparison tab opens locally generated evaluator `results.json` files and labels them as historical evidence. Raw experiment logs and databases are intentionally excluded from this repository. The test-fixture builder uses the separate document-authoring environment with ReportLab and pypdfium2; regenerating the provided PDFs is optional and pypdfium2 is not required to run the app.

## Project documentation

- [Planning changes and realistic fictional fixtures](docs/PLANNING_CHANGES.md)
- [Code walkthrough](docs/CODE_WALKTHROUGH.md)
- [Recorded evaluation findings and limitations](docs/EXPANDED_EVALUATION.md)
- [Technical source notes](docs/TECHNICAL_SOURCES.md)
- [Iteration 1 comparison-view increment](docs/ITERATION1_INCREMENT.md)

Historical notes retain their checkpoint-specific test counts. This repository also includes separately committed mixed-scan, CSV-validation, and experiment-manifest safeguards added during the staged uploads. The report PDF, recording script, and other local course documents are separate deliverables; their presence or submission is not implied by this repository.

## Remaining work

Trello setup and instructor invitations remain separate tasks. Videos are deferred. Further work includes a fresh untouched test set, broader semantic coverage, improved field editing, and final deliverable review. OCR and comprehensive holiday interpretation are not implemented. No redistribution license has been selected; dependencies retain their own license terms.
