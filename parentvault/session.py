"""Review-state boundary: edits invalidate approval and generated output.

Qt widgets are only a presentation layer. This class owns the rule that an
unreviewed or subsequently edited proposal cannot generate or save results.
Tests can therefore verify the approval workflow without clicking a window.
"""
from datetime import date
from .core import Schedule, calendar_rows, validate_grounding


class ReviewSession:
    def __init__(self):
        # The session holds source pages, the proposed schedule, approval, and generated rows for the current document.
        self.pages = []
        self.source_name = ''
        self.source_hash = ''
        self.schedule = None
        # Approval and generated dates are tied to a specific version of the rules.
        self.approved = False
        self.rows = []

    def invalidate(self):
        """Call immediately after any edit, even if that edit is currently invalid."""
        # Approval and generated dates are tied to a specific version of the rules.
        self.approved = False
        self.rows = []

    def replace_document(self, pages, name, digest):
        """A new source must not inherit a previous source's rules or approval."""
        self.invalidate()
        self.schedule = None
        # Copy the page list so the caller cannot change which pages this session reviews.
        self.pages = list(pages)
        self.source_name, self.source_hash = name, digest

    def propose(self, schedule: Schedule):
        """Install a validated proposal; this never grants user approval."""
        self.invalidate()
        # Check the proposal against the stored source before accepting it into the session.
        validate_grounding(schedule, self.pages)
        self.schedule = schedule

    def approve(self, json_text: str):
        """Reparse edited JSON so widget edits cannot bypass schema validation."""
        self.invalidate()
        # Read the current editor contents so approval applies to the user's latest edits.
        schedule = Schedule.model_validate_json(json_text)
        # Check the proposal against the stored source before accepting it into the session.
        validate_grounding(schedule, self.pages)
        # An unresolved warning means the repeating pattern may omit a provision, so approval stops here.
        if schedule.warnings:
            raise ValueError('Resolve unsupported or ambiguous provisions before approval')
        self.schedule = schedule
        self.approved = True

    def generate(self, start: date, end: date):
        if not self.approved or self.schedule is None:
            raise ValueError('Review and approve the current rules first')
        # Calculate from the approved schedule and retain the rows for display and export.
        self.rows = calendar_rows(self.schedule, start, end)
        return self.rows
