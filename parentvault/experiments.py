"""Run independent extraction methods without granting review approval."""
# Load time for use in this module.
import time
# Bring in baseline from core.
from .core import baseline
# Bring in extract_local from local_model.
from .local_model import extract_local


def compare_document(pages, model, expected=None, name='Current document', model_extractor=None):
    """Preserve each failure and measured runtime; never replace model failures.

    Expected values come from an explicitly reviewed rule set, or remain unknown.
    Agreement with reviewed values is not independent proof of interpretation.
    Raw request/response content is deliberately not persisted by this workflow.
    """
    # Keep both methods' outputs in the same case record for the comparison table.
    result = {'id': name, 'expected': expected}
    # Group baseline, local model in methods.
    methods = {'baseline': lambda: baseline(pages),
               'local_model': lambda: (model_extractor or extract_local)(pages, model)[0]}
    # Process each method, operation from items.
    for method, operation in methods.items():
        # Start a new timer for this method so its runtime excludes the other method.
        started = time.perf_counter()
        # Attempt this operation so its failure can be handled below.
        try:
            # Run the method independently and serialize its proposal for the result table.
            proposal = operation()
            # Group actual in selected result entry.
            result[method] = {'actual': proposal.model_dump(mode='json')}
        # Handle exception raised by the attempted operation.
        except Exception as error:
            # Preserve failures in the method's own row so the other result is still visible.
            result[method] = {'error': f'{type(error).__name__}: {error}'}
        result[method]['seconds'] = time.perf_counter() - started
    # Return result to the caller.
    return [result]
