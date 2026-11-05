"""Behavioral checks against explicit expected outcomes.

No model calls occur here: inference variability must not determine whether
calendar arithmetic or source checking is correct. The separate live runner
records real integration results and its failures independently.
"""
# Bring in date from datetime.
from datetime import date
# Load pytest for use in this module.
import pytest
# Bring in Schedule, Evidence, baseline, calendar_rows, validate_grounding from parentvault.core.
from parentvault.core import Schedule, Evidence, baseline, calendar_rows, validate_grounding
# Bring in extract_pdf from parentvault.core.
from parentvault.core import extract_pdf
# Load pymupdf for use in this module.
import pymupdf

# Set text to 'Beginning 2026-11-02, Parent A has seven consecutive ov'.
TEXT='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'

# Verify baseline source and calendar boundary.
def test_baseline_source_and_calendar_boundary():
    # Check the day before the anchor, both exchange boundaries, and wraparound.
    s=baseline([TEXT]); validate_grounding(s,[TEXT])
    # Set rows from calendar rows.
    rows=calendar_rows(s,date(2026,11,1),date(2026,11,16))
    assert [rows[i]['parent'] for i in (0,1,7,8,14,15)] == ['B','A','A','B','B','A']

# Verify pdf line wrap preserves baseline grounding.
def test_pdf_line_wrap_preserves_baseline_grounding():
    # Initialize pages as an ordered list of values.
    pages=[TEXT.replace(' followed by','\nfollowed by')]
    # Set baseline schedule from baseline.
    s=baseline(pages); validate_grounding(s,pages)

# Verify leap day and year rollover.
def test_leap_day_and_year_rollover():
    # Leap day remains within A's initial block. Year rollover must not skip a
    # day even though the month and year labels change together.
    s=baseline([TEXT]).model_copy(update={'anchor_date':date(2024,2,26)})
    # Verify that parent field equals 'A' before treating this check as successful.
    assert calendar_rows(s,date(2024,2,29),date(2024,2,29))[0]['parent']=='A'
    # Set rows from calendar rows.
    rows=calendar_rows(s,date(2024,12,31),date(2025,1,1))
    assert [r['date'] for r in rows]==['2024-12-31','2025-01-01']

# Verify ungrounded quote rejected.
def test_ungrounded_quote_rejected():
    # A valid schema alone cannot make a nonexistent source page acceptable.
    s=baseline([TEXT]); s.evidence=[Evidence(page=2,quote='invented')]
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): validate_grounding(s,[TEXT])

# Verify exception abstention and generation block.
def test_exception_abstention_and_generation_block():
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): baseline([TEXT+' Holidays override this rule.'])
    # Set baseline schedule from baseline.
    s=baseline([TEXT]); s.warnings=['Unresolved holiday override']
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): calendar_rows(s,date(2026,11,2),date(2026,11,3))

# Verify invalid cycle and missing anchor rejected.
def test_invalid_cycle_and_missing_anchor_rejected():
    data=baseline([TEXT]).model_dump(); data['cycle']=['A']*14
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): Schedule.model_validate(data)
    # Use pop on data.
    data=baseline([TEXT]).model_dump(); data.pop('anchor_date')
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): Schedule.model_validate(data)

# Verify real pdf extraction and image only rejection.
def test_real_pdf_extraction_and_image_only_rejection(tmp_path):
    # Build the file or folder path for path.
    path=tmp_path/'sample.pdf'
    # Set PDF document from open.
    doc=pymupdf.open(); page=doc.new_page()
    # Place fictional source text inside the PDF page bounds.
    page.insert_textbox(pymupdf.Rect(40,40,550,700),TEXT)
    # Write the binary contents to the destination file.
    path.write_bytes(doc.tobytes()); doc.close()
    # Set pages from extract pdf.
    pages=extract_pdf(path)
    # Verify that anchor date equals date before treating this check as successful.
    assert baseline(pages).anchor_date==date(2026,11,2)
    # Set PDF document from open.
    doc=pymupdf.open(); doc.new_page()
    # Write the binary contents to the destination file.
    path.write_bytes(doc.tobytes()); doc.close()
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='No readable text'): extract_pdf(path)

# Verify invalid range rejected.
def test_invalid_range_rejected():
    # Set baseline schedule from baseline.
    s=baseline([TEXT])
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): calendar_rows(s,date(2026,11,3),date(2026,11,2))


# Verify readable cover cannot hide scanned schedule page.
def test_readable_cover_cannot_hide_scanned_schedule_page(tmp_path):
    # Build a hybrid packet: text on page one, an image-only page two. An
    # extractor must not silently treat the readable subset as the whole plan.
    doc=pymupdf.open(); page=doc.new_page()
    # Use insert text on page.
    page.insert_text((40,40),'FICTIONAL research packet cover')
    # Set image from pixmap.
    image=pymupdf.Pixmap(pymupdf.csRGB,pymupdf.IRect(0,0,20,20),False)
    # Use clear with on image.
    image.clear_with(255)
    # Use insert image on page.
    page=doc.new_page(); page.insert_image(page.rect,pixmap=image)
    # Build the file or folder path for path.
    path=tmp_path/'hybrid.pdf'; path.write_bytes(doc.tobytes()); doc.close()
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='Pages 2.*OCR'):
        # Run extract pdf with the supplied input.
        extract_pdf(path)
