# Project and Portfolio IV

## ParentVault AI

I am developing a Windows desktop research application for turning supported text-based parenting-plan PDFs into reviewed recurring overnight calendars.

## Repository organization

I am importing the existing local project into this repository in stages: setup, extraction and validation, desktop workflow, then fictional fixtures and planning notes. Commit timestamps record when each batch is uploaded, not when the underlying work was first created.

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

The desktop interface and storage modules will arrive in the next import stage. The extractor now also rejects mixed packets containing image-only pages so a readable cover cannot hide a scanned schedule. Nine focused backend checks pass at this stage.
