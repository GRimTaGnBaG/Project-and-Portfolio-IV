"""Frozen-prompt synthetic evaluation with separate development/held-out cases.

The JSON manifest supplies authored scenarios and expected values. PDFs are
generated from those scenarios, then read through the same extraction function
as the application. Results are measured, never inferred from HTTP success.
"""
# Load argparse for use in this module.
import argparse
# Load hashlib for use in this module.
import hashlib
# Load json for use in this module.
import json
# Load time for use in this module.
import time
# Load re for use in this module.
import re
# Bring in date from datetime.
from datetime import date
# Bring in Path from pathlib.
from pathlib import Path
# Bring in uuid4 from uuid.
from uuid import uuid4
# Load pymupdf for use in this module.
import pymupdf
# Bring in extract_pdf, baseline from parentvault.core.
from parentvault.core import extract_pdf, baseline
# Bring in SYSTEM_PROMPT, extract_local from parentvault.local_model.
from parentvault.local_model import SYSTEM_PROMPT, extract_local

# Keep parent as root.
ROOT=Path(__file__).parent


def load_cases(path: Path):
    """Validate the experiment manifest before writing files or running models.

    IDs become filenames, so accept only bounded filename-safe identifiers.
    Duplicate IDs would overwrite evidence and inflate apparent case counts.
    Validate authored answer shapes up front so malformed keys cannot turn
    evaluation failures into misleading measurements after expensive inference.
    """
    # Set cases from loads.
    cases=json.loads(path.read_text(encoding='utf-8'))
    # Handle the case where there is no isinstance or there is no cases.
    if not isinstance(cases,list) or not cases:
        # Stop with a clear error explaining evaluation manifest must be a nonempty list.
        raise ValueError('Evaluation manifest must be a nonempty list')
    # Set seen from set.
    seen=set()
    # Process each case from cases.
    for case in cases:
        # Handle the case where there is no isinstance.
        if not isinstance(case,dict): raise ValueError('Each evaluation case must be an object')
        # Set identifier from get.
        identifier=case.get('id')
        # Handle the case where there is no isinstance or there is no fullmatch.
        if not isinstance(identifier,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',identifier):
            # Stop with a clear error explaining case ids must be filename-safe identifiers of at
            # most 80 characters.
            raise ValueError('Case IDs must be filename-safe identifiers of at most 80 characters')
        # Handle the case where identifier is in seen.
        if identifier in seen: raise ValueError('Duplicate case IDs would overwrite evidence')
        # Use add on seen.
        seen.add(identifier)
        # Handle the case where get is absent from 'development', 'held_out'.
        if case.get('split') not in ('development','held_out'):
            # Stop with a clear error explaining each case needs a development or held_out split.
            raise ValueError('Each case needs a development or held_out split')
        # Set kind from get.
        kind=case.get('kind')
        # Handle the case where kind is absent from 'week', 'pattern', 'reject'.
        if kind not in ('week','pattern','reject'): raise ValueError('Unsupported case kind')
        # Handle the case where kind equals 'reject'.
        if kind=='reject':
            # Handle the case where there is no isinstance or there is no strip.
            if not isinstance(case.get('text'),str) or not case['text'].strip():
                # Stop with a clear error explaining a rejection case requires explicit source
                # text.
                raise ValueError('A rejection case requires explicit source text')
            # Skip this entry and move to the next one.
            continue
        # Set anchor from get.
        anchor=case.get('anchor')
        # Attempt this operation so its failure can be handled below.
        try:
            # Choose parsed based on whether isinstance is present or true.
            parsed=date.fromisoformat(anchor) if isinstance(anchor,str) else None
        # Handle value error raised by the attempted operation.
        except ValueError as error:
            # Stop with a clear error explaining supported cases require a valid iso anchor date.
            raise ValueError('Supported cases require a valid ISO anchor date') from error
        # Handle the case where parsed is no value or isoformat differs from anchor.
        if parsed is None or parsed.isoformat()!=anchor:
            # Stop with a clear error explaining supported cases require a valid iso anchor date.
            raise ValueError('Supported cases require a valid ISO anchor date')
        # Handle the case where kind equals 'week'.
        if kind=='week':
            # Handle the case where get, get is absent from 'A', 'B', 'B', 'A'.
            if (case.get('first'),case.get('second')) not in (('A','B'),('B','A')):
                # Stop with a clear error explaining weekly cases require different a/b owners.
                raise ValueError('Weekly cases require different A/B owners')
        else:
            # Set cycle from get.
            cycle=case.get('cycle')
            if (not isinstance(cycle,list) or len(cycle)!=14 or
                any(owner not in ('A','B') for owner in cycle) or set(cycle)!={'A','B'}):
                # Stop with a clear error explaining pattern cases require fourteen a/b entries
                # containing both owners.
                raise ValueError('Pattern cases require fourteen A/B entries containing both owners')
    # Return cases to the caller.
    return cases


def case_text(case):
    """Author the input representation separately from the model response."""
    # Handle the case where kind field equals 'week'.
    if case['kind']=='week':
        # Return the result to the caller.
        return (f"Beginning {case['anchor']}, Parent {case['first']} has seven consecutive overnights, "
                f"followed by seven consecutive overnights with Parent {case['second']}. This 14-day cycle repeats.")
    # Handle the case where kind field equals 'pattern'.
    if case['kind']=='pattern':
        # Return the result to the caller.
        return (f"Anchor date: {case['anchor']}. The repeating 14-day overnight ownership pattern, "
                f"starting on that anchor date, is {', '.join(case['cycle'])}. A means Parent A; B means Parent B. "
                'The listed order is explicit; repeat it every 14 days.')
    # Return text field to the caller.
    return case['text']


def expected_fields(case):
    # Handle the case where kind field equals 'reject'.
    if case['kind']=='reject': return None
    cycle=case.get('cycle') or [case['first']]*7+[case['second']]*7
    # Return the result to the caller.
    return {'anchor_date':case['anchor'],'cycle':cycle,'exchange_weekday':None,'exchange_time':None}


def main():
    # Set parser from argument parser.
    parser=argparse.ArgumentParser(description=__doc__)
    # Define a command line option and how its value is interpreted.
    parser.add_argument('--split',choices=['development','held_out'],default='held_out')
    # Define a command line option and how its value is interpreted.
    parser.add_argument('--model',default='parentvault-research')
    # Set command line options from parse args.
    args=parser.parse_args()
    # Set cases from load cases.
    cases=load_cases(ROOT/'fixtures'/'evaluation_cases.json')
    # Build the file or folder path for output.
    output=ROOT/'data'/f'dataset-{args.split}-{uuid4().hex}'
    # Create the output directory before writing files into it.
    output.mkdir(parents=True)
    # Initialize results as an empty list.
    results=[]
    # Process each case from cases.
    for case in cases:
        # Handle the case where split field differs from split.
        if case['split']!=args.split: continue
        # Build the file or folder path for path.
        path=output/(case['id']+'.pdf')
        # Set PDF document from open.
        doc=pymupdf.open(); page=doc.new_page()
        # Place fictional source text inside the PDF page bounds.
        page.insert_textbox(pymupdf.Rect(50,50,550,730),
            'FICTIONAL TEST DOCUMENT - NOT A COURT ORDER\n\n'+case_text(case),fontsize=12)
        # Write the binary contents to the destination file.
        path.write_bytes(doc.tobytes()); doc.close()
        # Set pages from extract pdf.
        pages=extract_pdf(path)
        # Group id, kind, expected in row.
        row={'id':case['id'],'kind':case['kind'],'expected':expected_fields(case)}
        # Process each method from 'baseline', 'local_model'.
        for method in ('baseline','local_model'):
            # Set started from perf counter.
            started=time.perf_counter(); result={}
            # Attempt this operation so its failure can be handled below.
            try:
                # Choose schedule based on whether method equals 'baseline'.
                schedule=baseline(pages) if method=='baseline' else extract_local(
                    pages,args.model,evidence_path=output/(case['id']+'-request.json'))[0]
                result['actual']=schedule.model_dump(mode='json')
                # Set returned warnings field from whether warnings is present.
                result['returned_warnings']=bool(schedule.warnings)
                # Handle the case where expected field is no value.
                if row['expected'] is None:
                    # Set correct unsupported handling field from whether warnings is present.
                    result['correct_unsupported_handling']=bool(schedule.warnings)
                else:
                    # Build matches field by transforming the entries from items.
                    result['matches']={k:result['actual'][k]==v for k,v in row['expected'].items()}
                    result['exact_plan_match']=all(result['matches'].values()) and not schedule.warnings
            # Handle exception raised by the attempted operation.
            except Exception as error:
                result['error']=f'{type(error).__name__}: {error}'
                # Set rejected field to True.
                result['rejected']=True
                # Handle the case where expected field is no value.
                if row['expected'] is None:
                    # Rejection is safe blocking, not necessarily correct semantic
                    # understanding. Preserve the cause alongside the count.
                    result['correct_unsupported_handling']=True
            result['seconds']=time.perf_counter()-started
            # Keep result as selected row entry.
            row[method]=result
        # Add this item to the accumulating list.
        results.append(row)
        # Save the text or JSON output using the requested encoding.
        (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        # Print this result or output location for the research operator.
        print(case['id'],json.dumps({m:{k:v for k,v in row[m].items() if k!='actual'} for m in ('baseline','local_model')}),flush=True)

    # Group split, model, prompt sha256, case count in summary.
    summary={'split':args.split,'model':args.model,'prompt_sha256':hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),'case_count':len(results)}
    # Process each method from 'baseline', 'local_model'.
    for method in ('baseline','local_model'):
        # Build supported by transforming the entries from results.
        supported=[r for r in results if r['expected'] is not None]
        # Build unsupported by transforming the entries from results.
        unsupported=[r for r in results if r['expected'] is None]
        # Precision/recall score non-null field/value pairs. Incorrect supplied
        # values count as both a false positive and a missed expected value.
        tp=fp=fn=0
        # Process each row from supported.
        for row in supported:
            # Set actual from get.
            actual=row[method].get('actual',{})
            # Process each key, value from items.
            for key,value in row['expected'].items():
                # Set predicted from get.
                predicted=actual.get(key)
                # Handle the case where value is not no value.
                if value is not None:
                    # Handle the case where predicted equals value.
                    if predicted==value: tp+=1
                    else:
                        # Update the running false negative count total.
                        fn+=1
                        # Handle the case where predicted is not no value.
                        if predicted is not None: fp+=1
                # Handle the case where predicted is not no value.
                elif predicted is not None: fp+=1
        # Group exact supported plans, supported denominator, blocked unsupported, unsupported
        # denominator, tp, fp, fn, precision, recall, total rejections in selected summary entry.
        summary[method]={'exact_supported_plans':sum(r[method].get('exact_plan_match',False) for r in supported),
            'supported_denominator':len(supported),'blocked_unsupported':sum(r[method].get('correct_unsupported_handling',False) for r in unsupported),
            'unsupported_denominator':len(unsupported),'tp':tp,'fp':fp,'fn':fn,
            'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,
            'total_rejections':sum(r[method].get('rejected',False) for r in results)}
    # Save the text or JSON output using the requested encoding.
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    # Print this result or output location for the research operator.
    print(json.dumps(summary,indent=2),flush=True)
    # Print this result or output location for the research operator.
    print('Evidence:',output,flush=True)


# Run the entry point only when the file is launched directly.
if __name__=='__main__': main()
