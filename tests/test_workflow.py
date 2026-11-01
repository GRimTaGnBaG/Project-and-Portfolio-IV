"""Workflow checks use real domain/storage operations, not copies of their logic."""
from datetime import date
import csv
import pytest
from parentvault.core import baseline
from parentvault.session import ReviewSession
from parentvault.storage import Store, export_csv

TEXT='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'


def approved_session():
    session=ReviewSession()
    session.replace_document([TEXT],'fictional.pdf','test-digest')
    session.propose(baseline([TEXT]))
    session.approve(session.schedule.model_dump_json())
    return session


def test_edit_or_new_source_invalidates_generation():
    session=approved_session()
    session.generate(date(2026,11,2),date(2026,11,3))
    session.invalidate()
    assert session.rows==[]
    with pytest.raises(ValueError): session.generate(date(2026,11,2),date(2026,11,3))
    session=approved_session(); session.replace_document(['different'],'new.pdf','new')
    assert not session.approved and session.schedule is None


def test_sqlite_roundtrip_requires_new_approval_and_delete(tmp_path):
    store=Store(tmp_path/'research.sqlite3')
    session=approved_session()
    record_id=store.save("Parent A's fictional plan",session)
    loaded=store.load(record_id)
    assert loaded.schedule==session.schedule and loaded.source_hash=='test-digest'
    assert not loaded.approved
    loaded.approve(loaded.schedule.model_dump_json())
    assert loaded.generate(date(2026,11,2),date(2026,11,2))[0]['parent']=='A'
    store.delete(record_id)
    assert store.list_records()==[]


def test_csv_matches_generated_rows_and_protects_existing_file(tmp_path):
    rows=approved_session().generate(date(2026,11,2),date(2026,11,9))
    path=tmp_path/'calendar.csv'; export_csv(path,rows)
    with path.open(newline='') as f: assert list(csv.DictReader(f))==rows
    with pytest.raises(FileExistsError): export_csv(path,rows)


def test_bad_edit_cannot_leave_previous_approval():
    session=approved_session()
    with pytest.raises(ValueError): session.approve('{}')
    assert not session.approved and session.rows==[]
