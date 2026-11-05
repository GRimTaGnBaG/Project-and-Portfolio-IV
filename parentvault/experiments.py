"""Run independent extraction methods without granting review approval."""
import time
from .core import baseline
from .local_model import extract_local


def compare_document(pages, model, expected=None, name='Current document', model_extractor=None):
    """Preserve each failure and measured runtime; never replace model failures.

    Expected values come from an explicitly reviewed rule set, or remain unknown.
    Agreement with reviewed values is not independent proof of interpretation.
    Raw request/response content is deliberately not persisted by this workflow.
    """
    result = {'id': name, 'expected': expected}
    methods = {'baseline': lambda: baseline(pages),
               'local_model': lambda: (model_extractor or extract_local)(pages, model)[0]}
    for method, operation in methods.items():
        started = time.perf_counter()
        try:
            proposal = operation()
            result[method] = {'actual': proposal.model_dump(mode='json')}
        except Exception as error:
            result[method] = {'error': f'{type(error).__name__}: {error}'}
        result[method]['seconds'] = time.perf_counter() - started
    return [result]
