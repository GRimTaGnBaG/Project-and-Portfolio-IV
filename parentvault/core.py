"""Pure document/rule operations shared by the CLI, desktop app, and tests.

There are deliberately no Qt imports here. Keeping domain logic independent
from buttons and windows lets tests verify actual schedule behavior without
opening a desktop session or asking a language model to do date arithmetic.
"""

# Bring in date, timedelta from datetime.
from datetime import date, timedelta
# Bring in Path from pathlib.
from pathlib import Path
# Bring in Literal from typing.
from typing import Literal
# Load re for use in this module.
import re
# Load pymupdf for use in this module.
import pymupdf
# Bring in BaseModel, ConfigDict, Field, model_validator from pydantic.
from pydantic import BaseModel, ConfigDict, Field, model_validator

# This intentionally narrow grammar is also a semantic cross-check: it can
# verify explicit statements without asking the same model to judge itself.
WEEK_RULE = re.compile(r'Beginning (\d{4}-\d{2}-\d{2}), Parent ([AB]) has seven consecutive overnights, followed by seven consecutive overnights with Parent ([AB])\. This 14-day cycle repeats\.')
# Set exception terms from compile.
EXCEPTION_TERMS = re.compile(r'\bholiday\b|\bexcept\w*\b|\boverride\w*\b|\bconflict\w*\b|school break|\bnot specified\b|\bnot provided\b|\bno start date\b',re.I)


class Evidence(BaseModel):
    """A literal source passage, identified by its one-based PDF page number."""
    # Reject unexpected fields so invented metadata cannot silently enter storage.
    model_config = ConfigDict(extra='forbid', strict=True)
    # Set page from field.
    page: int = Field(ge=1)
    # Set quote from field.
    quote: str = Field(min_length=1)


class Schedule(BaseModel):
    """One explicit repeating pattern; cycle[0] belongs to anchor_date.

    Pydantic parses ISO date strings from JSON into real date objects. Ownership
    is restricted to neutral A/B labels. Evidence proves quotation membership,
    not that the entire interpretation is correct; human review remains vital.
    """
    # Set model config from config dict.
    model_config = ConfigDict(extra='forbid')
    anchor_date: date
    # Set cycle from field.
    cycle: list[Literal['A', 'B']] = Field(min_length=14, max_length=14)
    # Set evidence from field.
    evidence: list[Evidence] = Field(min_length=1)
    warnings: list[str]
    exchange_weekday: str | None
    exchange_time: str | None

    @model_validator(mode='after')
    def both_parents(self):
        # A one-parent pattern is outside this demonstrator's shared schedule scope.
        if set(self.cycle) != {'A', 'B'}:
            # Stop with a clear error explaining a supported cycle must contain both parent a and
            # parent b.
            raise ValueError('A supported cycle must contain both Parent A and Parent B')
        # Return self to the caller.
        return self


def extract_pdf(path: Path) -> list[str]:
    """Read bounded text PDFs and keep page boundaries for evidence checking.

    The context manager closes the PDF even if extraction raises an exception.
    No OCR is attempted: an image-only input must fail clearly, not look like a
    valid document containing an empty parenting plan.
    """
    # Handle the case where lower differs from '.pdf'.
    if path.suffix.lower() != '.pdf':
        # Stop with a clear error explaining select a pdf file.
        raise ValueError('Select a PDF file')
    # Handle the case where st size exceeds 10000000.
    if path.stat().st_size > 10_000_000:
        # Stop with a clear error explaining pdf exceeds the research limit of 10 mb.
        raise ValueError('PDF exceeds the research limit of 10 MB')
    # The context manager releases the PDF file even when validation raises an error.
    with pymupdf.open(path) as doc:
        # Handle the case where needs pass is present or true.
        if doc.needs_pass:
            # Stop with a clear error explaining encrypted pdfs are unsupported.
            raise ValueError('Encrypted PDFs are unsupported')
        if not 1 <= len(doc) <= 30:
            # Stop with a clear error explaining select a pdf containing 1 to 30 pages.
            raise ValueError('Select a PDF containing 1 to 30 pages')
        # Keep one string per page so evidence can be traced back to its source.
        pages = [p.get_text() for p in doc]
        # A readable cover must not hide scanned schedule pages later in a
        # packet. Remember image-bearing pages with no text before closing PDF.
        image_only_pages = [i+1 for i,p in enumerate(doc)
                            if not pages[i].strip() and p.get_images()]
    # Handle the case where there is no strip.
    if not ''.join(pages).strip():
        # Stop with a clear error explaining no readable text found; image-only pdfs require ocr.
        raise ValueError('No readable text found; image-only PDFs require OCR')
    # Handle the case where image only pages is present or true.
    if image_only_pages:
        # Set page numbers from join.
        page_numbers=', '.join(map(str,image_only_pages))
        # Pass the failure back to the caller.
        raise ValueError(f'Pages {page_numbers} contain images without readable text; OCR review is required')
    # Handle the case where sum exceeds 40000.
    if sum(map(len, pages)) > 40000:
        # Stop with a clear error explaining document exceeds the 40000-character research limit.
        raise ValueError('Document exceeds the 40000-character research limit')
    # Return pages to the caller.
    return pages


def normalize(text: str) -> str:
    """Collapse layout whitespace without changing spelling or punctuation."""
    # Return join to the caller.
    return ' '.join(text.split())


def validate_grounding(schedule: Schedule, pages: list[str]) -> None:
    """Require every proposed quote to occur on its claimed source page.

    Users see page numbers starting at one; Python lists start at zero. Convert
    only after checking the page is in range. This catches fabricated quotations,
    but does not establish that a quotation supports every individual field.
    """
    # Process each item from evidence.
    for item in schedule.evidence:
        # Handle the case where there is no normalize or page exceeds the number of pages or
        # normalize is absent from normalize.
        if not normalize(item.quote) or item.page > len(pages) or normalize(item.quote) not in normalize(pages[item.page-1]):
            # Stop with a clear error explaining source quotation does not match the referenced
            # page.
            raise ValueError('Source quotation does not match the referenced page')
    # Set text from normalize.
    text=normalize('\n'.join(pages))
    # Set explicit from list.
    explicit=list(WEEK_RULE.finditer(text))
    # Handle the case where explicit is present or true.
    if explicit:
        # Compare every explicit occurrence. Multiple contradictory statements
        # must fail rather than accepting whichever one a model happened to use.
        for match in explicit:
            # Expand the two parent labels into seven nights each, then check the proposal against the source.
            expected_cycle=[match[2]]*7+[match[3]]*7
            # Handle the case where isoformat differs from 1 field or cycle differs from expected
            # cycle.
            if schedule.anchor_date.isoformat()!=match[1] or schedule.cycle!=expected_cycle:
                # Stop with a clear error explaining proposed anchor/cycle contradicts an explicit
                # source rotation.
                raise ValueError('Proposed anchor/cycle contradicts an explicit source rotation')
    # Require a warning when the source mentions a possible exception. Approval later rejects any unresolved warnings.
    if EXCEPTION_TERMS.search(text) and not schedule.warnings:
        # Stop with a clear error explaining source contains possible exceptions; warnings cannot
        # be empty.
        raise ValueError('Source contains possible exceptions; warnings cannot be empty')


def baseline(pages: list[str]) -> Schedule:
    """Conservative benchmark: match one explicit alternating-week sentence.

    Abstention is an intentional result, not an AI fallback. The deliberately
    limited vocabulary gives the research comparison an understandable baseline.
    Whitespace normalization accounts for visual line wrapping in PDF extraction.
    """
    # Set text from normalize.
    text = normalize('\n'.join(pages))
    # Collect every matching clause so multiple rotations cannot silently turn into one proposal.
    matches = list(WEEK_RULE.finditer(text))
    # Handle the case where the number of matches differs from 1 or 2 field equals 3 field.
    if len(matches) != 1 or matches[0][2] == matches[0][3]:
        # Stop with a clear error explaining baseline cannot determine one supported alternating-
        # week rule.
        raise ValueError('Baseline cannot determine one supported alternating-week rule')
    # Handle the case where search is present or true.
    if EXCEPTION_TERMS.search(text):
        # Stop with a clear error explaining potential exception requires review; baseline
        # abstained.
        raise ValueError('Potential exception requires review; baseline abstained')
    # Keep 0 field as match.
    match = matches[0]
    # Regex group zero is the complete matched sentence. The numbered groups hold the date and the two parent labels.
    quote = match[0]
    # Set page from next.
    page = next((i+1 for i,p in enumerate(pages) if quote in normalize(p)), None)
    # Handle the case where page is no value.
    if page is None:
        # Stop with a clear error explaining rule spanning pages requires manual review.
        raise ValueError('Rule spanning pages requires manual review')
    # Set weekdays from findall.
    weekdays=re.findall(r'The regular exchange weekday is (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\.',text)
    # Set times from findall.
    times=re.findall(r'The regular exchange time is ((?:[01]\d|2[0-3]):[0-5]\d)\.',text)
    # Handle the case where the number of set exceeds 1 or the number of set exceeds 1.
    if len(set(weekdays))>1 or len(set(times))>1:
        # Stop with a clear error explaining conflicting exchange metadata requires review.
        raise ValueError('Conflicting exchange metadata requires review')
    # Return schedule to the caller.
    return Schedule(anchor_date=match[1], cycle=[match[2]]*7+[match[3]]*7,
                    evidence=[Evidence(page=page,quote=quote)], warnings=[],
                    exchange_weekday=weekdays[0] if weekdays else None,
                    exchange_time=times[0] if times else None)


def calendar_rows(schedule: Schedule, start: date, end: date):
    """Return inclusive overnight rows with no AI involved in the calculation.

    Subtract the anchor to find the offset, then use modulo 14 to wrap it into
    the cycle. Python's modulo also handles negative offsets: the day before
    the anchor maps to index 13. Reject unresolved warnings before any output.
    This function expects reviewed input; the session layer enforces approval.
    """
    # Handle the case where warnings is present or true.
    if schedule.warnings:
        # Stop with a clear error explaining resolve flagged provisions before generating a
        # calendar.
        raise ValueError('Resolve flagged provisions before generating a calendar')
    # Handle the case where end is below start or days exceeds 366.
    if end < start or (end-start).days > 366:
        # Stop with a clear error explaining choose an ordered range of at most 367 dates.
        raise ValueError('Choose an ordered range of at most 367 dates')
    # The extra one includes the final requested date rather than excluding it.
    rows = []
    # Process each offset from range.
    for offset in range((end-start).days+1):
        # Convert the loop offset into an actual calendar date.
        day = start + timedelta(days=offset)
        # Subtract the anchor date to find the offset. Modulo wraps it into slots 0 through 13, including dates before the anchor.
        cycle_index = (day-schedule.anchor_date).days % 14
        # Store one ISO date and owner per row. The table and CSV consume this same structure.
        rows.append({'date': day.isoformat(), 'parent': schedule.cycle[cycle_index]})
    # Return rows to the caller.
    return rows
