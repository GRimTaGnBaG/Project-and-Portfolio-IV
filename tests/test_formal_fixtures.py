"""Verify authored fixture outcomes without trusting model-generated answers."""
# Bring in Path from pathlib.
from pathlib import Path
# Load pytest for use in this module.
import pytest
# Bring in extract_pdf, baseline, validate_grounding, Schedule, Evidence from parentvault.core.
from parentvault.core import extract_pdf,baseline,validate_grounding,Schedule,Evidence

# Build the file or folder path for fixtures.
FIXTURES=Path(__file__).resolve().parents[1]/'fixtures'


# Verify supported formal packet preserves page grounding.
def test_supported_formal_packet_preserves_page_grounding():
    # Set pages from extract pdf.
    pages=extract_pdf(FIXTURES/'formal_recurring_plan.pdf')
    # Verify that the number of pages equals 5 before treating this check as successful.
    assert len(pages)==5
    # Set schedule from baseline.
    schedule=baseline(pages)
    # Verify that isoformat equals '2026-11-02' before treating this check as successful.
    assert schedule.anchor_date.isoformat()=='2026-11-02'
    assert schedule.cycle==['A']*7+['B']*7
    # Verify that page equals 3 before treating this check as successful.
    assert schedule.evidence[0].page==3
    # Verify that exchange weekday equals 'Monday' and exchange time equals '18:00' before
    # treating this check as successful.
    assert schedule.exchange_weekday=='Monday' and schedule.exchange_time=='18:00'


# Verify exception packet requires abstention.
def test_exception_packet_requires_abstention():
    # Set pages from extract pdf.
    pages=extract_pdf(FIXTURES/'formal_plan_with_exceptions.pdf')
    # Verify that the number of pages equals 7 before treating this check as successful.
    assert len(pages)==7
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='exception'): baseline(pages)


# Verify scanned fictional packet is not silently accepted.
def test_scanned_fictional_packet_is_not_silently_accepted():
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='No readable text'):
        # Run extract pdf with the supplied input.
        extract_pdf(FIXTURES/'formal_recurring_plan_scanned.pdf')


# Verify valid json with wrong rotation is rejected.
def test_valid_json_with_wrong_rotation_is_rejected():
    # Set pages from extract pdf.
    pages=extract_pdf(FIXTURES/'formal_recurring_plan.pdf')
    # Set schedule from baseline.
    schedule=baseline(pages)
    schedule.cycle=['A','B']*7
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='contradicts'): validate_grounding(schedule,pages)


# Verify model cannot silently drop document exceptions.
def test_model_cannot_silently_drop_document_exceptions():
    # Set clean from extract pdf.
    clean=extract_pdf(FIXTURES/'formal_recurring_plan.pdf')
    # Set complex pages from extract pdf.
    complex_pages=extract_pdf(FIXTURES/'formal_plan_with_exceptions.pdf')
    # Set schedule from baseline.
    schedule=baseline(clean)
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='exceptions'): validate_grounding(schedule,complex_pages)


# Verify missing ownership is not filled without warning.
def test_missing_ownership_is_not_filled_without_warning():
    # This reproduces the held-out failure: schema-valid invented ownership
    # must not erase an explicit statement that the remaining days are unknown.
    text='Beginning 2027-02-01, Parent A has the first three overnights. Remaining overnight ownership is not specified.'
    # Set schedule from schedule.
    schedule=Schedule(anchor_date='2027-02-01',cycle=['A']*7+['B']*7,
        evidence=[Evidence(page=1,quote=text)],warnings=[],exchange_weekday=None,exchange_time=None)
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='exceptions'): validate_grounding(schedule,[text])
