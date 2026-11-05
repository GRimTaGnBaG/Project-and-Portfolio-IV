"""Convert retained experiment results into explicit, readable comparison rows.

This module does not run a model or change a review session. Saved evidence is
historical: an error must remain visible, and an absent field is not equivalent
to an explicitly returned null. Keeping this transformation separate from Qt
lets tests check result interpretation without a window or inference server.
"""
# Load json for use in this module.
import json
# Bring in Path from pathlib.
from pathlib import Path

# Keep 'anchor_date', 'cycle', 'exchange_weekday', 'exchange_time' as fields.
FIELDS = ('anchor_date','cycle','exchange_weekday','exchange_time')
# Keep 'Case', 'Method', 'Field', 'Expected', 'Recorded output', 'Result', 'Seconds' as headers.
HEADERS = ('Case','Method','Field','Expected','Recorded output','Result','Seconds')


def display(value):
    """Use JSON notation to distinguish null, arrays, and strings clearly."""
    # Return the result to the caller.
    return json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value


def load_comparison(path: Path, formal_answers: dict | None = None):
    """Read results.json from either evaluator; reject request/summary files.

    A size bound avoids freezing the GUI on accidentally selected large logs.
    Formal results identify their expected scenario by a label, so their authored
    answer manifest supplies field values. Dataset results include those values.
    Missing answer keys are labeled unknown rather than treated as correctness.
    """
    # Handle the case where st size exceeds 2000000.
    if path.stat().st_size>2_000_000:
        # Stop with a clear error explaining choose a results json file smaller than 2 mb.
        raise ValueError('Choose a results JSON file smaller than 2 MB')
    # Set results from loads.
    results=json.loads(path.read_text(encoding='utf-8'))
    # Handle the case where there is no isinstance or there is no results.
    if not isinstance(results,list) or not results:
        # Stop with a clear error explaining choose an evaluator results.json file, not a request
        # log or summary.
        raise ValueError('Choose an evaluator results.json file, not a request log or summary')
    # Initialize rows as an empty list.
    rows=[]
    # Process each case from results.
    for case in results:
        # Handle the case where there is no isinstance or there is no isinstance.
        if not isinstance(case,dict) or not isinstance(case.get('fixture',case.get('id')),str):
            # Stop with a clear error explaining every result must identify a fixture or case.
            raise ValueError('Every result must identify a fixture or case')
        # Set name from get.
        name=case.get('fixture',case.get('id'))
        # Handle the case where 'input_error' is in case.
        if 'input_error' in case:
            # Add this item to the accumulating list.
            rows.append([name,'Input','document','Readable text required',str(case['input_error']),
                         'Input rejected','—'])
            # Skip this entry and move to the next one.
            continue
        # Set expected from get.
        expected=case.get('expected')
        # Handle the case where there is no isinstance.
        if not isinstance(expected,dict):
            # Set manifest from get.
            manifest=(formal_answers or {}).get(name,{})
            # Build expected by transforming the entries from fields.
            expected={field:manifest[field] for field in FIELDS if field in manifest}
        unsupported=(case.get('kind')=='reject' or case.get('expected')=='block_for_unsupported_or_missing_provisions')
        # Set found to False.
        found=False
        # Process each method from 'baseline', 'local_model'.
        for method in ('baseline','local_model'):
            # Handle the case where method is absent from case.
            if method not in case: continue
            # Set found to True.
            found=True
            # Keep selected case entry as result.
            result=case[method]
            # Handle the case where there is no isinstance.
            if not isinstance(result,dict): raise ValueError('Method results must be JSON objects')
            # Set elapsed from get.
            elapsed=result.get('seconds',result.get('elapsed_seconds'))
            # Handle the case where elapsed is not no value and isinstance is present or true or
            # there is no isinstance or elapsed is below 0.
            if elapsed is not None and (isinstance(elapsed,bool) or not isinstance(elapsed,(int,float)) or elapsed<0):
                # Stop with a clear error explaining runtime must be a nonnegative number.
                raise ValueError('Runtime must be a nonnegative number')
            # Choose seconds based on whether elapsed is not no value.
            seconds=f'{elapsed:.2f}' if elapsed is not None else 'Not recorded'
            # Handle the case where get is present or true.
            if result.get('error'):
                # Do not turn network or validation errors into claims that the
                # model understood an unsupported document. Preserve the cause.
                rows.append([name,method,'execution','Usable grounded result',str(result['error']),
                             'Error / abstention',seconds])
                # Skip this entry and move to the next one.
                continue
            # Set actual from get.
            actual=result.get('actual',result.get('schedule'))
            # Handle the case where there is no isinstance.
            if not isinstance(actual,dict): raise ValueError('A successful result must contain recorded rule fields')
            # Handle the case where unsupported is present or true.
            if unsupported:
                # Set warned from whether get is present.
                warned=bool(actual.get('warnings'))
                # Add this item to the accumulating list.
                rows.append([name,method,'unsupported provisions','Warnings / blocked approval',
                             display(actual.get('warnings')), 'Warnings recorded' if warned else 'MISSED WARNING',seconds])
            # Process each field from fields.
            for field in FIELDS:
                known=field in expected
                present=field in actual
                # Choose status based on whether known is present or true and present is present
                # or true.
                status=('Match' if actual.get(field)==expected.get(field) else 'MISMATCH') if known and present else (
                    'Missing output' if known else 'Answer key unavailable')
                # Add this item to the accumulating list.
                rows.append([name,method,field,display(expected[field]) if known else 'Not specified in answer key',
                             display(actual[field]) if present else '<no recorded field>',status,seconds])
        # Handle the case where there is no found.
        if not found: raise ValueError('No baseline or local_model results were found')
    # Return rows to the caller.
    return rows
