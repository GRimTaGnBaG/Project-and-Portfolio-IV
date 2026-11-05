"""Repeatable extraction experiment using a generated fictional PDF.

The default run measures the baseline without requiring LM Studio. --live adds
a real request and compares anchor/cycle with the known baseline for this one
case. That comparison is a smoke check, not held-out accuracy measurement.
"""
# Bring in Path from pathlib.
from pathlib import Path
# Load json for use in this module.
import json
# Load argparse for use in this module.
import argparse
# Load pymupdf for use in this module.
import pymupdf
# Bring in extract_pdf, baseline from parentvault.core.
from parentvault.core import extract_pdf,baseline
# Bring in extract_local from parentvault.local_model.
from parentvault.local_model import extract_local

# Set parser from argument parser.
parser=argparse.ArgumentParser(description=__doc__)
# Define a command line option and how its value is interpreted.
parser.add_argument('--live',action='store_true')
# Define a command line option and how its value is interpreted.
parser.add_argument('--model',default='parentvault-research')
# Set command line options from parse args.
args=parser.parse_args()
# Keep parent as root.
root=Path(__file__).parent
# Build the file or folder path for fixtures.
fixtures=root/'fixtures'; fixtures.mkdir(exist_ok=True)
# Build the file or folder path for evidence.
evidence=root/'evidence'; evidence.mkdir(exist_ok=True)
# This fixture encodes a hand-checkable scenario: A begins on November 2,
# switches to B on November 9, and repeats from A on November 16.
text='Fictional research fixture. No real people or court order.\n\nBeginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'
# Build the file or folder path for path.
path=fixtures/'alternating_week.pdf'
# Set PDF document from open.
doc=pymupdf.open(); page=doc.new_page(); page.insert_textbox(pymupdf.Rect(50,50,550,700),text,fontsize=12); pdf_bytes=doc.tobytes(); doc.close(); path.write_bytes(pdf_bytes)
# Set pages from extract pdf.
pages=extract_pdf(path)
# Set baseline schedule from baseline.
s=baseline(pages)
# Save the text or JSON output using the requested encoding.
(evidence/'baseline.json').write_text(s.model_dump_json(indent=2),encoding='utf-8')
# Print this result or output location for the research operator.
print('PDF extraction and baseline passed')
# Handle the case where live is present or true.
if args.live:
    # The full request/response stays local by default. This includes the exact
    # system and user prompts required for later reporting and reproducibility.
    result,record=extract_local(pages,args.model,evidence_path=evidence/'live_request_response.json')
    # Save the text or JSON output using the requested encoding.
    (evidence/'live_request_response.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    # Save the text or JSON output using the requested encoding.
    (evidence/'live_schedule.json').write_text(result.model_dump_json(indent=2),encoding='utf-8')
    # Print this result or output location for the research operator.
    print('Live model response validated; seconds:',round(record['elapsed_seconds'],2))
    # Print this result or output location for the research operator.
    print('Matches baseline:',result.anchor_date==s.anchor_date and result.cycle==s.cycle)
