"""Real live integration check, without silently granting user approval.

Run after reviewing the fictional fixture and its known answer key. The explicit
--approve-fictional flag is the research operator's approval for this test case;
it is not a general bypass for documents loaded in the desktop application.
"""
# Load argparse for use in this module.
import argparse
# Load csv for use in this module.
import csv
# Load hashlib for use in this module.
import hashlib
# Load json for use in this module.
import json
# Bring in date from datetime.
from datetime import date
# Bring in Path from pathlib.
from pathlib import Path
# Bring in uuid4 from uuid.
from uuid import uuid4
# Bring in extract_pdf from parentvault.core.
from parentvault.core import extract_pdf
# Bring in extract_local from parentvault.local_model.
from parentvault.local_model import extract_local
# Bring in ReviewSession from parentvault.session.
from parentvault.session import ReviewSession
# Bring in Store, export_csv from parentvault.storage.
from parentvault.storage import Store, export_csv


def main():
    # Set parser from argument parser.
    parser=argparse.ArgumentParser(description=__doc__)
    # Define a command line option and how its value is interpreted.
    parser.add_argument('--model',default='parentvault-research')
    # Define a command line option and how its value is interpreted.
    parser.add_argument('--approve-fictional',action='store_true',required=True)
    # Set command line options from parse args.
    args=parser.parse_args()
    # Keep parent as root.
    root=Path(__file__).parent
    # Build the file or folder path for path.
    path=root/'fixtures'/'alternating_week.pdf'
    # Every run receives its own directory so measurements and exported rows
    # remain distinguishable rather than being replaced by the next experiment.
    output=root/'data'/f'integration-{uuid4().hex}'
    # Create the output directory before writing files into it.
    output.mkdir(parents=True)
    # Set pages from extract pdf.
    pages=extract_pdf(path)
    # Set schedule, record from extract local.
    schedule,record=extract_local(pages,args.model,evidence_path=output/'request_response.json')
    # This expected result is written independently of the returned model data.
    # A response must be correct for the known case, not merely parseable JSON.
    assert schedule.anchor_date==date(2026,11,2)
    assert schedule.cycle==['A']*7+['B']*7
    # Set session from review session.
    session=ReviewSession()
    # Use replace document on session.
    session.replace_document(pages,path.name,hashlib.sha256(path.read_bytes()).hexdigest())
    # Use propose on session.
    session.propose(schedule)
    # Use approve on session.
    session.approve(schedule.model_dump_json())
    # Set rows from generate.
    rows=session.generate(date(2026,11,1),date(2026,11,30))
    # Verify that the number of rows equals 30 and parent field equals 'B' and parent field equals
    # 'B' before treating this check as successful.
    assert len(rows)==30 and rows[0]['parent']=='B' and rows[8]['parent']=='B'
    # Set store from store.
    store=Store(output/'research.sqlite3')
    record_id=store.save('Fictional integration verification',session)
    # Set loaded from load.
    loaded=store.load(record_id)
    # Verify that there is no approved before treating this check as successful.
    assert not loaded.approved  # Loading cannot inherit a fresh review decision.
    # Use approve on loaded.
    loaded.approve(loaded.schedule.model_dump_json())
    # Verify that generate equals rows before treating this check as successful.
    assert loaded.generate(date(2026,11,1),date(2026,11,30))==rows
    # Run export csv with the supplied input.
    export_csv(output/'calendar.csv',rows)
    # Use a managed context for open file so exit handling runs automatically.
    with (output/'calendar.csv').open(newline='') as f:
        # Verify that list equals rows before treating this check as successful.
        assert list(csv.DictReader(f))==rows
    # Group model, elapsed inference seconds, row count, pdf to model to review to database to csv
    # in result.
    result={'model':args.model,'elapsed_inference_seconds':record['elapsed_seconds'],
            'row_count':len(rows),'pdf_to_model_to_review_to_database_to_csv':'passed'}
    # Save the text or JSON output using the requested encoding.
    (output/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    # Print this result or output location for the research operator.
    print(json.dumps(result,indent=2))
    # Print this result or output location for the research operator.
    print('Evidence:',output)


# Run the entry point only when the file is launched directly.
if __name__=='__main__':
    # Run the script workflow from its command line entry point.
    main()
