"""Measure longer fictional fixtures without converting failures into successes.

Each case retains its own request log. A valid response must also match expected
fields or correctly abstain; schema validity is not scored as factual accuracy.
"""
# Bring in Path from pathlib.
from pathlib import Path
# Bring in datetime, timezone from datetime.
from datetime import datetime, timezone
# Bring in uuid4 from uuid.
from uuid import uuid4
# Load json for use in this module.
import json
# Load time for use in this module.
import time
# Bring in extract_pdf, baseline from parentvault.core.
from parentvault.core import extract_pdf, baseline
# Bring in extract_local from parentvault.local_model.
from parentvault.local_model import extract_local

# Keep parent as root.
ROOT=Path(__file__).parent


def main():
    # Set answers from loads.
    answers=json.loads((ROOT/'fixtures'/'formal_fixture_answers.json').read_text())
    # Build the file or folder path for output.
    output=ROOT/'data'/f'formal-evaluation-{uuid4().hex}'
    # Create the output directory before writing files into it.
    output.mkdir(parents=True)
    # Initialize results as an empty list.
    results=[]
    # Process each filename, answer from items.
    for filename,answer in answers.items():
        # Group fixture, expected in case.
        case={'fixture':filename,'expected':answer['expected']}
        # Attempt this operation so its failure can be handled below.
        try:
            # Set pages from extract pdf.
            pages=extract_pdf(ROOT/'fixtures'/filename)
            # Set pages field from the number of pages.
            case['pages']=len(pages)
        # Handle exception raised by the attempted operation.
        except Exception as error:
            # Set input error field from str.
            case['input_error']=str(error)
            case['correct_input_rejection']=answer['expected']=='reject_no_readable_text'
            # Add this item to the accumulating list.
            results.append(case)
            # Skip this entry and move to the next one.
            continue
        # Process each method from 'baseline', 'local_model'.
        for method in ('baseline','local_model'):
            # Set started from perf counter.
            started=time.perf_counter()
            # Group the named values in result.
            result={}
            # Attempt this operation so its failure can be handled below.
            try:
                # Handle the case where method equals 'baseline'.
                if method=='baseline':
                    # Set schedule from baseline.
                    schedule=baseline(pages)
                else:
                    # Set schedule,  from extract local.
                    schedule,_=extract_local(pages,'parentvault-research',evidence_path=output/(filename+'.json'))
                result['schedule']=schedule.model_dump(mode='json')
                # Set abstained field from whether warnings is present.
                result['abstained']=bool(schedule.warnings)
                # Handle the case where expected field equals 'reviewable_recurring_plan'.
                if answer['expected']=='reviewable_recurring_plan':
                    # Four independently authored field values are evaluated;
                    # evidence page correctness is reported separately.
                    fields=['anchor_date','cycle','exchange_weekday','exchange_time']
                    actual=schedule.model_dump(mode='json')
                    # Build field matches field by transforming the entries from fields.
                    result['field_matches']={field:actual[field]==answer[field] for field in fields}
                    result['complete_match']=all(result['field_matches'].values()) and not schedule.warnings
                    # Set correct rule page field from any.
                    result['correct_rule_page']=any(e.page==answer['rule_page'] for e in schedule.evidence)
                else:
                    # Set correct abstention field from whether warnings is present.
                    result['correct_abstention']=bool(schedule.warnings)
            # Handle exception raised by the attempted operation.
            except Exception as error:
                result['error']=f'{type(error).__name__}: {error}'
                # Failure is reported separately; it is not a successful semantic
                # abstention from a usable model response.
                result['abstained']=True
            result['elapsed_seconds']=time.perf_counter()-started
            # Keep result as selected case entry.
            case[method]=result
        # Add this item to the accumulating list.
        results.append(case)
        # Save the text or JSON output using the requested encoding.
        (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        # Print this result or output location for the research operator.
        print(filename,':',json.dumps({m:{k:v for k,v in case[m].items() if k!='schedule'} for m in ('baseline','local_model')}),flush=True)
    # Save the text or JSON output using the requested encoding.
    (output/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    # Print this result or output location for the research operator.
    print('Evidence:',output,flush=True)


# Run the entry point only when the file is launched directly.
if __name__=='__main__': main()
