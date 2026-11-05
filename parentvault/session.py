"""Review-state boundary: edits invalidate approval and generated output.

Qt widgets are only a presentation layer. This class owns the rule that an
unreviewed or subsequently edited proposal cannot generate or save results.
Tests can therefore verify the approval workflow without clicking a window.
"""
# Bring in date from datetime.
from datetime import date
# Bring in Schedule, calendar_rows, validate_grounding from core.
from .core import Schedule, calendar_rows, validate_grounding


# Group the state and behavior for the review session.
class ReviewSession:
    def __init__(self):
        # The session holds source pages, the proposed schedule, approval, and generated rows for the current document.
        self.pages = []
        # Set source name to ''.
        self.source_name = ''
        # Set source hash to ''.
        self.source_hash = ''
        # Set schedule to no value.
        self.schedule = None
        # Approval and generated dates are tied to a specific version of the rules.
        self.approved = False
        # Initialize rows as an empty list.
        self.rows = []

    def invalidate(self):
        """Call immediately after any edit, even if that edit is currently invalid."""
        # Approval and generated dates are tied to a specific version of the rules.
        self.approved = False
        # Initialize rows as an empty list.
        self.rows = []

    def replace_document(self, pages, name, digest):
        """A new source must not inherit a previous source's rules or approval."""
        # Clear approval and calendar rows because the source or rules are changing.
        self.invalidate()
        # Set schedule to no value.
        self.schedule = None
        # Copy the page list so the caller cannot change which pages this session reviews.
        self.pages = list(pages)
        # Keep name, digest as source name, source hash.
        self.source_name, self.source_hash = name, digest

    def propose(self, schedule: Schedule):
        """Install a validated proposal; this never grants user approval."""
        # Clear approval and calendar rows because the source or rules are changing.
        self.invalidate()
        # Check the proposal against the stored source before accepting it into the session.
        validate_grounding(schedule, self.pages)
        # Keep schedule as schedule.
        self.schedule = schedule

    def approve(self, json_text: str):
        """Reparse edited JSON so widget edits cannot bypass schema validation."""
        # Clear approval and calendar rows because the source or rules are changing.
        self.invalidate()
        # Read the current editor contents so approval applies to the user's latest edits.
        schedule = Schedule.model_validate_json(json_text)
        # Check the proposal against the stored source before accepting it into the session.
        validate_grounding(schedule, self.pages)
        # An unresolved warning means the repeating pattern may omit a provision, so approval stops here.
        if schedule.warnings:
            # Stop with a clear error explaining resolve unsupported or ambiguous provisions
            # before approval.
            raise ValueError('Resolve unsupported or ambiguous provisions before approval')
        # Keep schedule as schedule.
        self.schedule = schedule
        # Set approved to True.
        self.approved = True

    # Produce the selected month from the approved recurring schedule.
    def generate(self, start: date, end: date):
        # Handle the case where there is no approved or schedule is no value.
        if not self.approved or self.schedule is None:
            # Stop with a clear error explaining review and approve the current rules first.
            raise ValueError('Review and approve the current rules first')
        # Calculate from the approved schedule and retain the rows for display and export.
        self.rows = calendar_rows(self.schedule, start, end)
        # Return rows to the caller.
        return self.rows
