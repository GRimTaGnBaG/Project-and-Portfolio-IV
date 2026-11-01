"""Review-state boundary: edits invalidate approval and generated output.

Qt widgets are only a presentation layer. This class owns the rule that an
unreviewed or subsequently edited proposal cannot generate or save results.
Tests can therefore verify the approval workflow without clicking a window.
"""
from datetime import date
from .core import Schedule, calendar_rows, validate_grounding


class ReviewSession:
    def __init__(self):
        self.pages = []
        self.source_name = ''
        self.source_hash = ''
        self.schedule = None
        self.approved = False
        self.rows = []

    def invalidate(self):
        """Call immediately after any edit, even if that edit is currently invalid."""
        self.approved = False
        self.rows = []

    def replace_document(self, pages, name, digest):
        """A new source must not inherit a previous source's rules or approval."""
        self.invalidate()
        self.schedule = None
        self.pages = list(pages)
        self.source_name, self.source_hash = name, digest

    def propose(self, schedule: Schedule):
        """Install a validated proposal; this never grants user approval."""
        self.invalidate()
        validate_grounding(schedule, self.pages)
        self.schedule = schedule

    def approve(self, json_text: str):
        """Reparse edited JSON so widget edits cannot bypass schema validation."""
        self.invalidate()
        schedule = Schedule.model_validate_json(json_text)
        validate_grounding(schedule, self.pages)
        if schedule.warnings:
            raise ValueError('Resolve unsupported or ambiguous provisions before approval')
        self.schedule = schedule
        self.approved = True

    def generate(self, start: date, end: date):
        if not self.approved or self.schedule is None:
            raise ValueError('Review and approve the current rules first')
        self.rows = calendar_rows(self.schedule, start, end)
        return self.rows
