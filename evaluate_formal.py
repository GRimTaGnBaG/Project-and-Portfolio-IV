"""Measure longer fictional fixtures without converting failures into successes.

Each case retains its own request log. A valid response must also match expected
fields or correctly abstain; schema validity is not scored as factual accuracy.
"""
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import json
import time
from parentvault.core import extract_pdf, baseline
from parentvault.local_model import extract_local

ROOT=Path(__file__).parent


def main():
    answers=json.loads((ROOT/'fixtures'/'formal_fixture_answers.json').read_text())
    output=ROOT/'data'/f'formal-evaluation-{uuid4().hex}'
    output.mkdir(parents=True)
    results=[]
    for filename,answer in answers.items():
        case={'fixture':filename,'expected':answer['expected']}
        try:
            pages=extract_pdf(ROOT/'fixtures'/filename)
            case['pages']=len(pages)
        except Exception as error:
            case['input_error']=str(error)
            case['correct_input_rejection']=answer['expected']=='reject_no_readable_text'
            results.append(case)
            continue
        for method in ('baseline','local_model'):
            started=time.perf_counter()
            result={}
            try:
                if method=='baseline':
                    schedule=baseline(pages)
                else:
                    schedule,_=extract_local(pages,'parentvault-research',evidence_path=output/(filename+'.json'))
                result['schedule']=schedule.model_dump(mode='json')
                result['abstained']=bool(schedule.warnings)
                if answer['expected']=='reviewable_recurring_plan':
                    # Four independently authored field values are evaluated;
                    # evidence page correctness is reported separately.
                    fields=['anchor_date','cycle','exchange_weekday','exchange_time']
                    actual=schedule.model_dump(mode='json')
                    result['field_matches']={field:actual[field]==answer[field] for field in fields}
                    result['complete_match']=all(result['field_matches'].values()) and not schedule.warnings
                    result['correct_rule_page']=any(e.page==answer['rule_page'] for e in schedule.evidence)
                else:
                    result['correct_abstention']=bool(schedule.warnings)
            except Exception as error:
                result['error']=f'{type(error).__name__}: {error}'
                # Failure is reported separately; it is not a successful semantic
                # abstention from a usable model response.
                result['abstained']=True
            result['elapsed_seconds']=time.perf_counter()-started
            case[method]=result
        results.append(case)
        (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        print(filename,':',json.dumps({m:{k:v for k,v in case[m].items() if k!='schedule'} for m in ('baseline','local_model')}),flush=True)
    (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('Evidence:',output,flush=True)


if __name__=='__main__': main()
