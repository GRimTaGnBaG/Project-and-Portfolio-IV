# Project and Portfolio IV — ParentVault AI

ParentVault is a Windows desktop MVP that turns supported text-based parenting-plan PDFs into reviewed recurring overnight calendars. The interface follows the five Figma pages: Document, Review Rules, Calendar, Saved Records, and Research Comparison.

## Run

Double-click **Start ParentVault.cmd**. The configured computer already has its Python dependencies. For a fresh Windows setup, install Python 3.12, run **Setup ParentVault.cmd**, then start the app. [Step-by-step user guide](docs/RUNNING_PARENTVAULT.md).

Try **Open sample plan → Baseline extraction → review and approve → Calendar → Generate approved month**. The fictional November sample produces 30 dates, including Parent B on November 1 and Parent A on November 2–8. Baseline mode works without LM Studio.

Local model mode requires LM Studio's server at `http://127.0.0.1:1235/v1`. Use **Check local model connection** and the exact model identifier; the tested alias is `parentvault-research`. No model download is performed by the application.

## Completed workflow

- Native PDF preview and extracted source pages.
- Separate baseline and local-model extraction with structured validation and source quotations.
- Editable anchor, 14-day rotation and exchange fields; edits invalidate approval.
- Explicit review acknowledgment before generation or saving.
- Parent-labeled monthly calendar and validated CSV export.
- Local SQLite save, search, load and confirmed delete; reload always requires review again.
- Fresh baseline/model comparison with measured runtimes, preserved failures, optional reviewed reference and summary export; historical result viewing remains available.
- One-click Windows launcher and local data separated from source updates.

## Supported scope

Text PDFs: up to 10 MB, 30 pages and 40,000 characters. One explicitly anchored repeating 14-day A/B overnight pattern. Scans require OCR, which is not implemented. Holiday overrides, missing schedules and comprehensive court-order interpretation remain unsupported. Model output and source quotation matches still require human review. Overnight assignments are not precise handoff instructions.

Saved plans and the latest comparison summary live in `%LOCALAPPDATA%\ParentVault`. Tests can override this with `PARENTVAULT_DATA_DIR`. Raw interactive model requests/responses are not written to disk. Research runners may explicitly archive evidence; raw logs, databases and credentials are excluded from Git.

## Verification and research

```powershell
python -m pytest -q
python run_research.py
python evaluate_dataset.py --split held_out --model "YOUR_LOADED_MODEL_IDENTIFIER"
```

The November 4 checkpoint passes **38 tests**, including actual PDF-to-calendar persistence and comparison-state checks. A separate live local-model desktop integration verifies the complete fictional-sample workflow. Tests do not make model calls; the live verification is reported separately. Earlier evaluation results remain historical and are not replaced by current results. Repeated cases are not untouched held-out evidence.

## Documentation

- [Run the application and troubleshoot](docs/RUNNING_PARENTVAULT.md)
- [Desktop design checkpoint](docs/DESKTOP_DESIGN.md)
- [Planning and fictional fixtures](docs/PLANNING_CHANGES.md)
- [Code walkthrough](docs/CODE_WALKTHROUGH.md)
- [Recorded evaluation findings](docs/EXPANDED_EVALUATION.md)
- [Technical sources](docs/TECHNICAL_SOURCES.md)
- [Iteration 1 increment](docs/ITERATION1_INCREMENT.md)

Historical documents retain their original checkpoint counts. Course reports and recordings are separate deliverables. This app's completion does not imply those items have been submitted. Dependencies retain their own license terms; no redistribution license has been selected for the project.
