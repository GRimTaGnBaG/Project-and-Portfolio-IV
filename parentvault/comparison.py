"""Convert retained experiment results into explicit, readable comparison rows.

This module does not run a model or change a review session. Saved evidence is
historical: an error must remain visible, and an absent field is not equivalent
to an explicitly returned null. Keeping this transformation separate from Qt
lets tests check result interpretation without a window or inference server.
"""
import json
from pathlib import Path

FIELDS = ('anchor_date','cycle','exchange_weekday','exchange_time')
HEADERS = ('Case','Method','Field','Expected','Recorded output','Result','Seconds')


def display(value):
    """Use JSON notation to distinguish null, arrays, and strings clearly."""
    return json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value


def load_comparison(path: Path, formal_answers: dict | None = None):
    """Read results.json from either evaluator; reject request/summary files.

    A size bound avoids freezing the GUI on accidentally selected large logs.
    Formal results identify their expected scenario by a label, so their authored
    answer manifest supplies field values. Dataset results include those values.
    Missing answer keys are labeled unknown rather than treated as correctness.
    """
    if path.stat().st_size>2_000_000:
        raise ValueError('Choose a results JSON file smaller than 2 MB')
    results=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(results,list) or not results:
        raise ValueError('Choose an evaluator results.json file, not a request log or summary')
    rows=[]
    for case in results:
        if not isinstance(case,dict) or not isinstance(case.get('fixture',case.get('id')),str):
            raise ValueError('Every result must identify a fixture or case')
        name=case.get('fixture',case.get('id'))
        if 'input_error' in case:
            rows.append([name,'Input','document','Readable text required',str(case['input_error']),
                         'Input rejected','—'])
            continue
        expected=case.get('expected')
        if not isinstance(expected,dict):
            manifest=(formal_answers or {}).get(name,{})
            expected={field:manifest[field] for field in FIELDS if field in manifest}
        unsupported=(case.get('kind')=='reject' or case.get('expected')=='block_for_unsupported_or_missing_provisions')
        found=False
        for method in ('baseline','local_model'):
            if method not in case: continue
            found=True
            result=case[method]
            if not isinstance(result,dict): raise ValueError('Method results must be JSON objects')
            elapsed=result.get('seconds',result.get('elapsed_seconds'))
            if elapsed is not None and (isinstance(elapsed,bool) or not isinstance(elapsed,(int,float)) or elapsed<0):
                raise ValueError('Runtime must be a nonnegative number')
            seconds=f'{elapsed:.2f}' if elapsed is not None else 'Not recorded'
            if result.get('error'):
                # Do not turn network or validation errors into claims that the
                # model understood an unsupported document. Preserve the cause.
                rows.append([name,method,'execution','Usable grounded result',str(result['error']),
                             'Error / abstention',seconds])
                continue
            actual=result.get('actual',result.get('schedule'))
            if not isinstance(actual,dict): raise ValueError('A successful result must contain recorded rule fields')
            if unsupported:
                warned=bool(actual.get('warnings'))
                rows.append([name,method,'unsupported provisions','Warnings / blocked approval',
                             display(actual.get('warnings')), 'Warnings recorded' if warned else 'MISSED WARNING',seconds])
            for field in FIELDS:
                known=field in expected
                present=field in actual
                status=('Match' if actual.get(field)==expected.get(field) else 'MISMATCH') if known and present else (
                    'Missing output' if known else 'Answer key unavailable')
                rows.append([name,method,field,display(expected[field]) if known else 'Not specified in answer key',
                             display(actual[field]) if present else '<no recorded field>',status,seconds])
        if not found: raise ValueError('No baseline or local_model results were found')
    return rows
