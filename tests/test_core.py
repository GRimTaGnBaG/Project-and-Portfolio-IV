"""Behavioral checks against explicit expected outcomes.

No model calls occur here: inference variability must not determine whether
calendar arithmetic or source checking is correct. The separate live runner
records real integration results and its failures independently.
"""
from datetime import date
import pytest
from parentvault.core import Schedule, Evidence, baseline, calendar_rows, validate_grounding
from parentvault.core import extract_pdf
import pymupdf

TEXT='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'

def test_baseline_source_and_calendar_boundary():
    # Check the day before the anchor, both exchange boundaries, and wraparound.
    s=baseline([TEXT]); validate_grounding(s,[TEXT])
    rows=calendar_rows(s,date(2026,11,1),date(2026,11,16))
    assert [rows[i]['parent'] for i in (0,1,7,8,14,15)] == ['B','A','A','B','B','A']

def test_pdf_line_wrap_preserves_baseline_grounding():
    pages=[TEXT.replace(' followed by','\nfollowed by')]
    s=baseline(pages); validate_grounding(s,pages)

def test_leap_day_and_year_rollover():
    # Leap day remains within A's initial block. Year rollover must not skip a
    # day even though the month and year labels change together.
    s=baseline([TEXT]).model_copy(update={'anchor_date':date(2024,2,26)})
    assert calendar_rows(s,date(2024,2,29),date(2024,2,29))[0]['parent']=='A'
    rows=calendar_rows(s,date(2024,12,31),date(2025,1,1))
    assert [r['date'] for r in rows]==['2024-12-31','2025-01-01']

def test_ungrounded_quote_rejected():
    # A valid schema alone cannot make a nonexistent source page acceptable.
    s=baseline([TEXT]); s.evidence=[Evidence(page=2,quote='invented')]
    with pytest.raises(ValueError): validate_grounding(s,[TEXT])

def test_exception_abstention_and_generation_block():
    with pytest.raises(ValueError): baseline([TEXT+' Holidays override this rule.'])
    s=baseline([TEXT]); s.warnings=['Unresolved holiday override']
    with pytest.raises(ValueError): calendar_rows(s,date(2026,11,2),date(2026,11,3))

def test_invalid_cycle_and_missing_anchor_rejected():
    data=baseline([TEXT]).model_dump(); data['cycle']=['A']*14
    with pytest.raises(ValueError): Schedule.model_validate(data)
    data=baseline([TEXT]).model_dump(); data.pop('anchor_date')
    with pytest.raises(ValueError): Schedule.model_validate(data)

def test_real_pdf_extraction_and_image_only_rejection(tmp_path):
    path=tmp_path/'sample.pdf'
    doc=pymupdf.open(); page=doc.new_page()
    page.insert_textbox(pymupdf.Rect(40,40,550,700),TEXT)
    path.write_bytes(doc.tobytes()); doc.close()
    pages=extract_pdf(path)
    assert baseline(pages).anchor_date==date(2026,11,2)
    doc=pymupdf.open(); doc.new_page()
    path.write_bytes(doc.tobytes()); doc.close()
    with pytest.raises(ValueError,match='No readable text'): extract_pdf(path)

def test_invalid_range_rejected():
    s=baseline([TEXT])
    with pytest.raises(ValueError): calendar_rows(s,date(2026,11,3),date(2026,11,2))
