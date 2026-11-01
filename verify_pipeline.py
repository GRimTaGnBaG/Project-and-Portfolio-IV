"""Real live integration check, without silently granting user approval.

Run after reviewing the fictional fixture and its known answer key. The explicit
--approve-fictional flag is the research operator's approval for this test case;
it is not a general bypass for documents loaded in the desktop application.
"""
import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path
from uuid import uuid4
from parentvault.core import extract_pdf
from parentvault.local_model import extract_local
from parentvault.session import ReviewSession
from parentvault.storage import Store, export_csv


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',default='parentvault-research')
    parser.add_argument('--approve-fictional',action='store_true',required=True)
    args=parser.parse_args()
    root=Path(__file__).parent
    path=root/'fixtures'/'alternating_week.pdf'
    # Every run receives its own directory so measurements and exported rows
    # remain distinguishable rather than being replaced by the next experiment.
    output=root/'data'/f'integration-{uuid4().hex}'
    output.mkdir(parents=True)
    pages=extract_pdf(path)
    schedule,record=extract_local(pages,args.model,evidence_path=output/'request_response.json')
    # This expected result is written independently of the returned model data.
    # A response must be correct for the known case, not merely parseable JSON.
    assert schedule.anchor_date==date(2026,11,2)
    assert schedule.cycle==['A']*7+['B']*7
    session=ReviewSession()
    session.replace_document(pages,path.name,hashlib.sha256(path.read_bytes()).hexdigest())
    session.propose(schedule)
    session.approve(schedule.model_dump_json())
    rows=session.generate(date(2026,11,1),date(2026,11,30))
    assert len(rows)==30 and rows[0]['parent']=='B' and rows[8]['parent']=='B'
    store=Store(output/'research.sqlite3')
    record_id=store.save('Fictional integration verification',session)
    loaded=store.load(record_id)
    assert not loaded.approved  # Loading cannot inherit a fresh review decision.
    loaded.approve(loaded.schedule.model_dump_json())
    assert loaded.generate(date(2026,11,1),date(2026,11,30))==rows
    export_csv(output/'calendar.csv',rows)
    with (output/'calendar.csv').open(newline='') as f:
        assert list(csv.DictReader(f))==rows
    result={'model':args.model,'elapsed_inference_seconds':record['elapsed_seconds'],
            'row_count':len(rows),'pdf_to_model_to_review_to_database_to_csv':'passed'}
    (output/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    print('Evidence:',output)


if __name__=='__main__':
    main()
