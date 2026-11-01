"""Verify authored fixture outcomes without trusting model-generated answers."""
from pathlib import Path
import pytest
from parentvault.core import extract_pdf,baseline,validate_grounding,Schedule,Evidence

FIXTURES=Path(__file__).resolve().parents[1]/'fixtures'


def test_supported_formal_packet_preserves_page_grounding():
    pages=extract_pdf(FIXTURES/'formal_recurring_plan.pdf')
    assert len(pages)==5
    schedule=baseline(pages)
    assert schedule.anchor_date.isoformat()=='2026-11-02'
    assert schedule.cycle==['A']*7+['B']*7
    assert schedule.evidence[0].page==3
    assert schedule.exchange_weekday=='Monday' and schedule.exchange_time=='18:00'


def test_exception_packet_requires_abstention():
    pages=extract_pdf(FIXTURES/'formal_plan_with_exceptions.pdf')
    assert len(pages)==7
    with pytest.raises(ValueError,match='exception'): baseline(pages)


def test_scanned_fictional_packet_is_not_silently_accepted():
    with pytest.raises(ValueError,match='No readable text'):
        extract_pdf(FIXTURES/'formal_recurring_plan_scanned.pdf')


def test_valid_json_with_wrong_rotation_is_rejected():
    pages=extract_pdf(FIXTURES/'formal_recurring_plan.pdf')
    schedule=baseline(pages)
    schedule.cycle=['A','B']*7
    with pytest.raises(ValueError,match='contradicts'): validate_grounding(schedule,pages)


def test_model_cannot_silently_drop_document_exceptions():
    clean=extract_pdf(FIXTURES/'formal_recurring_plan.pdf')
    complex_pages=extract_pdf(FIXTURES/'formal_plan_with_exceptions.pdf')
    schedule=baseline(clean)
    with pytest.raises(ValueError,match='exceptions'): validate_grounding(schedule,complex_pages)


def test_missing_ownership_is_not_filled_without_warning():
    # This reproduces the held-out failure: schema-valid invented ownership
    # must not erase an explicit statement that the remaining days are unknown.
    text='Beginning 2027-02-01, Parent A has the first three overnights. Remaining overnight ownership is not specified.'
    schedule=Schedule(anchor_date='2027-02-01',cycle=['A']*7+['B']*7,
        evidence=[Evidence(page=1,quote=text)],warnings=[],exchange_weekday=None,exchange_time=None)
    with pytest.raises(ValueError,match='exceptions'): validate_grounding(schedule,[text])
