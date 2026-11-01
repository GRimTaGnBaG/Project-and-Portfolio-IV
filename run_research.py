"""Repeatable extraction experiment using a generated fictional PDF.

The default run measures the baseline without requiring LM Studio. --live adds
a real request and compares anchor/cycle with the known baseline for this one
case. That comparison is a smoke check, not held-out accuracy measurement.
"""
from pathlib import Path
import json
import argparse
import pymupdf
from parentvault.core import extract_pdf,baseline
from parentvault.local_model import extract_local

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--live',action='store_true')
parser.add_argument('--model',default='parentvault-research')
args=parser.parse_args()
root=Path(__file__).parent
fixtures=root/'fixtures'; fixtures.mkdir(exist_ok=True)
evidence=root/'evidence'; evidence.mkdir(exist_ok=True)
# This fixture encodes a hand-checkable scenario: A begins on November 2,
# switches to B on November 9, and repeats from A on November 16.
text='Fictional research fixture. No real people or court order.\n\nBeginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'
path=fixtures/'alternating_week.pdf'
doc=pymupdf.open(); page=doc.new_page(); page.insert_textbox(pymupdf.Rect(50,50,550,700),text,fontsize=12); pdf_bytes=doc.tobytes(); doc.close(); path.write_bytes(pdf_bytes)
pages=extract_pdf(path)
s=baseline(pages)
(evidence/'baseline.json').write_text(s.model_dump_json(indent=2),encoding='utf-8')
print('PDF extraction and baseline passed')
if args.live:
    # The full request/response stays local by default. This includes the exact
    # system and user prompts required for later reporting and reproducibility.
    result,record=extract_local(pages,args.model,evidence_path=evidence/'live_request_response.json')
    (evidence/'live_request_response.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    (evidence/'live_schedule.json').write_text(result.model_dump_json(indent=2),encoding='utf-8')
    print('Live model response validated; seconds:',round(record['elapsed_seconds'],2))
    print('Matches baseline:',result.anchor_date==s.anchor_date and result.cycle==s.cycle)
