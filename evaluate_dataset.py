"""Frozen-prompt synthetic evaluation with separate development/held-out cases.

The JSON manifest supplies authored scenarios and expected values. PDFs are
generated from those scenarios, then read through the same extraction function
as the application. Results are measured, never inferred from HTTP success.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
from uuid import uuid4
import pymupdf
from parentvault.core import extract_pdf, baseline
from parentvault.local_model import SYSTEM_PROMPT, extract_local

ROOT=Path(__file__).parent


def case_text(case):
    """Author the input representation separately from the model response."""
    if case['kind']=='week':
        return (f"Beginning {case['anchor']}, Parent {case['first']} has seven consecutive overnights, "
                f"followed by seven consecutive overnights with Parent {case['second']}. This 14-day cycle repeats.")
    if case['kind']=='pattern':
        return (f"Anchor date: {case['anchor']}. The repeating 14-day overnight ownership pattern, "
                f"starting on that anchor date, is {', '.join(case['cycle'])}. A means Parent A; B means Parent B. "
                'The listed order is explicit; repeat it every 14 days.')
    return case['text']


def expected_fields(case):
    if case['kind']=='reject': return None
    cycle=case.get('cycle') or [case['first']]*7+[case['second']]*7
    return {'anchor_date':case['anchor'],'cycle':cycle,'exchange_weekday':None,'exchange_time':None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split',choices=['development','held_out'],default='held_out')
    parser.add_argument('--model',default='parentvault-research')
    args=parser.parse_args()
    cases=json.loads((ROOT/'fixtures'/'evaluation_cases.json').read_text())
    output=ROOT/'data'/f'dataset-{args.split}-{uuid4().hex}'
    output.mkdir(parents=True)
    results=[]
    for case in cases:
        if case['split']!=args.split: continue
        path=output/(case['id']+'.pdf')
        doc=pymupdf.open(); page=doc.new_page()
        page.insert_textbox(pymupdf.Rect(50,50,550,730),
            'FICTIONAL TEST DOCUMENT - NOT A COURT ORDER\n\n'+case_text(case),fontsize=12)
        path.write_bytes(doc.tobytes()); doc.close()
        pages=extract_pdf(path)
        row={'id':case['id'],'kind':case['kind'],'expected':expected_fields(case)}
        for method in ('baseline','local_model'):
            started=time.perf_counter(); result={}
            try:
                schedule=baseline(pages) if method=='baseline' else extract_local(
                    pages,args.model,evidence_path=output/(case['id']+'-request.json'))[0]
                result['actual']=schedule.model_dump(mode='json')
                result['returned_warnings']=bool(schedule.warnings)
                if row['expected'] is None:
                    result['correct_unsupported_handling']=bool(schedule.warnings)
                else:
                    result['matches']={k:result['actual'][k]==v for k,v in row['expected'].items()}
                    result['exact_plan_match']=all(result['matches'].values()) and not schedule.warnings
            except Exception as error:
                result['error']=f'{type(error).__name__}: {error}'
                result['rejected']=True
                if row['expected'] is None:
                    # Rejection is safe blocking, not necessarily correct semantic
                    # understanding. Preserve the cause alongside the count.
                    result['correct_unsupported_handling']=True
            result['seconds']=time.perf_counter()-started
            row[method]=result
        results.append(row)
        (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        print(case['id'],json.dumps({m:{k:v for k,v in row[m].items() if k!='actual'} for m in ('baseline','local_model')}),flush=True)

    summary={'split':args.split,'model':args.model,'prompt_sha256':hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),'case_count':len(results)}
    for method in ('baseline','local_model'):
        supported=[r for r in results if r['expected'] is not None]
        unsupported=[r for r in results if r['expected'] is None]
        # Precision/recall score non-null field/value pairs. Incorrect supplied
        # values count as both a false positive and a missed expected value.
        tp=fp=fn=0
        for row in supported:
            actual=row[method].get('actual',{})
            for key,value in row['expected'].items():
                predicted=actual.get(key)
                if value is not None:
                    if predicted==value: tp+=1
                    else:
                        fn+=1
                        if predicted is not None: fp+=1
                elif predicted is not None: fp+=1
        summary[method]={'exact_supported_plans':sum(r[method].get('exact_plan_match',False) for r in supported),
            'supported_denominator':len(supported),'blocked_unsupported':sum(r[method].get('correct_unsupported_handling',False) for r in unsupported),
            'unsupported_denominator':len(unsupported),'tp':tp,'fp':fp,'fn':fn,
            'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,
            'total_rejections':sum(r[method].get('rejected',False) for r in results)}
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)
    print('Evidence:',output,flush=True)


if __name__=='__main__': main()
