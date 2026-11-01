"""Pure document/rule operations shared by the CLI, desktop app, and tests.

There are deliberately no Qt imports here. Keeping domain logic independent
from buttons and windows lets tests verify actual schedule behavior without
opening a desktop session or asking a language model to do date arithmetic.
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Literal
import re
import pymupdf
from pydantic import BaseModel, ConfigDict, Field, model_validator

# This intentionally narrow grammar is also a semantic cross-check: it can
# verify explicit statements without asking the same model to judge itself.
WEEK_RULE = re.compile(r'Beginning (\d{4}-\d{2}-\d{2}), Parent ([AB]) has seven consecutive overnights, followed by seven consecutive overnights with Parent ([AB])\. This 14-day cycle repeats\.')
EXCEPTION_TERMS = re.compile(r'\bholiday\b|\bexcept\w*\b|\boverride\w*\b|\bconflict\w*\b|school break|\bnot specified\b|\bnot provided\b|\bno start date\b',re.I)


class Evidence(BaseModel):
    """A literal source passage, identified by its one-based PDF page number."""
    # Reject unexpected fields so invented metadata cannot silently enter storage.
    model_config = ConfigDict(extra='forbid', strict=True)
    page: int = Field(ge=1)
    quote: str = Field(min_length=1)


class Schedule(BaseModel):
    """One explicit repeating pattern; cycle[0] belongs to anchor_date.

    Pydantic parses ISO date strings from JSON into real date objects. Ownership
    is restricted to neutral A/B labels. Evidence proves quotation membership,
    not that the entire interpretation is correct; human review remains vital.
    """
    model_config = ConfigDict(extra='forbid')
    anchor_date: date
    cycle: list[Literal['A', 'B']] = Field(min_length=14, max_length=14)
    evidence: list[Evidence] = Field(min_length=1)
    warnings: list[str]
    exchange_weekday: str | None
    exchange_time: str | None

    @model_validator(mode='after')
    def both_parents(self):
        # A one-parent pattern is outside this demonstrator's shared schedule scope.
        if set(self.cycle) != {'A', 'B'}:
            raise ValueError('A supported cycle must contain both Parent A and Parent B')
        return self


def extract_pdf(path: Path) -> list[str]:
    """Read bounded text PDFs and keep page boundaries for evidence checking.

    The context manager closes the PDF even if extraction raises an exception.
    No OCR is attempted: an image-only input must fail clearly, not look like a
    valid document containing an empty parenting plan.
    """
    if path.suffix.lower() != '.pdf':
        raise ValueError('Select a PDF file')
    if path.stat().st_size > 10_000_000:
        raise ValueError('PDF exceeds the research limit of 10 MB')
    with pymupdf.open(path) as doc:
        if doc.needs_pass:
            raise ValueError('Encrypted PDFs are unsupported')
        if not 1 <= len(doc) <= 30:
            raise ValueError('Select a PDF containing 1 to 30 pages')
        pages = [p.get_text() for p in doc]
        # A readable cover must not hide scanned schedule pages later in a
        # packet. Remember image-bearing pages with no text before closing PDF.
        image_only_pages = [i+1 for i,p in enumerate(doc)
                            if not pages[i].strip() and p.get_images()]
    if not ''.join(pages).strip():
        raise ValueError('No readable text found; image-only PDFs require OCR')
    if image_only_pages:
        page_numbers=', '.join(map(str,image_only_pages))
        raise ValueError(f'Pages {page_numbers} contain images without readable text; OCR review is required')
    if sum(map(len, pages)) > 40000:
        raise ValueError('Document exceeds the 40000-character research limit')
    return pages


def normalize(text: str) -> str:
    """Collapse layout whitespace without changing spelling or punctuation."""
    return ' '.join(text.split())


def validate_grounding(schedule: Schedule, pages: list[str]) -> None:
    """Require every proposed quote to occur on its claimed source page.

    Users see page numbers starting at one; Python lists start at zero. Convert
    only after checking the page is in range. This catches fabricated quotations,
    but does not establish that a quotation supports every individual field.
    """
    for item in schedule.evidence:
        if not normalize(item.quote) or item.page > len(pages) or normalize(item.quote) not in normalize(pages[item.page-1]):
            raise ValueError('Source quotation does not match the referenced page')
    text=normalize('\n'.join(pages))
    explicit=list(WEEK_RULE.finditer(text))
    if explicit:
        # Compare every explicit occurrence. Multiple contradictory statements
        # must fail rather than accepting whichever one a model happened to use.
        for match in explicit:
            expected_cycle=[match[2]]*7+[match[3]]*7
            if schedule.anchor_date.isoformat()!=match[1] or schedule.cycle!=expected_cycle:
                raise ValueError('Proposed anchor/cycle contradicts an explicit source rotation')
    if EXCEPTION_TERMS.search(text) and not schedule.warnings:
        raise ValueError('Source contains possible exceptions; warnings cannot be empty')


def baseline(pages: list[str]) -> Schedule:
    """Conservative benchmark: match one explicit alternating-week sentence.

    Abstention is an intentional result, not an AI fallback. The deliberately
    limited vocabulary gives the research comparison an understandable baseline.
    Whitespace normalization accounts for visual line wrapping in PDF extraction.
    """
    text = normalize('\n'.join(pages))
    matches = list(WEEK_RULE.finditer(text))
    if len(matches) != 1 or matches[0][2] == matches[0][3]:
        raise ValueError('Baseline cannot determine one supported alternating-week rule')
    if EXCEPTION_TERMS.search(text):
        raise ValueError('Potential exception requires review; baseline abstained')
    match = matches[0]
    quote = match[0]
    page = next((i+1 for i,p in enumerate(pages) if quote in normalize(p)), None)
    if page is None:
        raise ValueError('Rule spanning pages requires manual review')
    weekdays=re.findall(r'The regular exchange weekday is (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\.',text)
    times=re.findall(r'The regular exchange time is ((?:[01]\d|2[0-3]):[0-5]\d)\.',text)
    if len(set(weekdays))>1 or len(set(times))>1:
        raise ValueError('Conflicting exchange metadata requires review')
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
    if schedule.warnings:
        raise ValueError('Resolve flagged provisions before generating a calendar')
    if end < start or (end-start).days > 366:
        raise ValueError('Choose an ordered range of at most 367 dates')
    # The extra one includes the final requested date rather than excluding it.
    rows = []
    for offset in range((end-start).days+1):
        day = start + timedelta(days=offset)
        cycle_index = (day-schedule.anchor_date).days % 14
        rows.append({'date': day.isoformat(), 'parent': schedule.cycle[cycle_index]})
    return rows
