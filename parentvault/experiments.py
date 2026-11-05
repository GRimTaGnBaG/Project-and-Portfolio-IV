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
    # Keep both methods' outputs in the same case record for the comparison table.
    result = {'id': name, 'expected': expected}
    methods = {'baseline': lambda: baseline(pages),
               'local_model': lambda: (model_extractor or extract_local)(pages, model)[0]}
    for method, operation in methods.items():
        # Start a new timer for this method so its runtime excludes the other method.
        started = time.perf_counter()
        try:
            # Run the method independently and serialize its proposal for the result table.
            proposal = operation()
            result[method] = {'actual': proposal.model_dump(mode='json')}
        except Exception as error:
            # Preserve failures in the method's own row so the other result is still visible.
            result[method] = {'error': f'{type(error).__name__}: {error}'}
        result[method]['seconds'] = time.perf_counter() - started
    return [result]
