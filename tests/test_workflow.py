"""Workflow checks use real domain/storage operations, not copies of their logic."""
# Bring in date from datetime.
from datetime import date
# Load csv for use in this module.
import csv
# Load pytest for use in this module.
import pytest
# Bring in baseline from parentvault.core.
from parentvault.core import baseline
# Bring in ReviewSession from parentvault.session.
from parentvault.session import ReviewSession
# Bring in Store, export_csv from parentvault.storage.
from parentvault.storage import Store, export_csv

# Set text to 'Beginning 2026-11-02, Parent A has seven consecutive ov'.
TEXT='Beginning 2026-11-02, Parent A has seven consecutive overnights, followed by seven consecutive overnights with Parent B. This 14-day cycle repeats.'


def approved_session():
    # Set session from review session.
    session=ReviewSession()
    # Use replace document on session.
    session.replace_document([TEXT],'fictional.pdf','test-digest')
    # Use propose on session.
    session.propose(baseline([TEXT]))
    # Use approve on session.
    session.approve(session.schedule.model_dump_json())
    # Return session to the caller.
    return session


# Verify edit or new source invalidates generation.
def test_edit_or_new_source_invalidates_generation():
    # Set session from approved session.
    session=approved_session()
    # Use generate on session.
    session.generate(date(2026,11,2),date(2026,11,3))
    # Clear approval and calendar rows because the source or rules are changing.
    session.invalidate()
    # Verify that rows equals  before treating this check as successful.
    assert session.rows==[]
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): session.generate(date(2026,11,2),date(2026,11,3))
    # Set session from approved session.
    session=approved_session(); session.replace_document(['different'],'new.pdf','new')
    # Verify that there is no approved and schedule is no value before treating this check as
    # successful.
    assert not session.approved and session.schedule is None


# Verify sqlite roundtrip requires new approval and delete.
def test_sqlite_roundtrip_requires_new_approval_and_delete(tmp_path):
    # Set store from store.
    store=Store(tmp_path/'research.sqlite3')
    # Set session from approved session.
    session=approved_session()
    record_id=store.save("Parent A's fictional plan",session)
    # Set loaded from load.
    loaded=store.load(record_id)
    # Verify that schedule equals schedule and source hash equals 'test-digest' before treating
    # this check as successful.
    assert loaded.schedule==session.schedule and loaded.source_hash=='test-digest'
    # Verify that there is no approved before treating this check as successful.
    assert not loaded.approved
    # Use approve on loaded.
    loaded.approve(loaded.schedule.model_dump_json())
    # Verify that parent field equals 'A' before treating this check as successful.
    assert loaded.generate(date(2026,11,2),date(2026,11,2))[0]['parent']=='A'
    # Use delete on store.
    store.delete(record_id)
    # Verify that list records equals  before treating this check as successful.
    assert store.list_records()==[]


# Verify csv matches generated rows and protects existing file.
def test_csv_matches_generated_rows_and_protects_existing_file(tmp_path):
    # Set rows from generate.
    rows=approved_session().generate(date(2026,11,2),date(2026,11,9))
    # Build the file or folder path for path.
    path=tmp_path/'calendar.csv'; export_csv(path,rows)
    # Use a managed context for open file so exit handling runs automatically.
    with path.open(newline='') as f: assert list(csv.DictReader(f))==rows
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(FileExistsError): export_csv(path,rows)


# Verify bad edit cannot leave previous approval.
def test_bad_edit_cannot_leave_previous_approval():
    # Set session from approved session.
    session=approved_session()
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): session.approve('{}')
    # Verify that there is no approved and rows equals  before treating this check as successful.
    assert not session.approved and session.rows==[]


# Verify invalid export cannot truncate an existing file.
def test_invalid_export_cannot_truncate_an_existing_file(tmp_path):
    # Build the file or folder path for path.
    path=tmp_path/'existing.csv'; path.write_text('retained original export')
    # Initialize rows as an ordered list of values.
    rows=[{'date':'2026-11-02','parent':'A'},{'date':'2026-11-03','parent':'=unexpected'}]
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): export_csv(path,rows,overwrite=True)
    # Verify that read text equals 'retained original export' before treating this check as
    # successful.
    assert path.read_text()=='retained original export'
    # Build the file or folder path for new path.
    new_path=tmp_path/'new.csv'
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError): export_csv(new_path,rows)
    # Verify that there is no exists before treating this check as successful.
    assert not new_path.exists()


# Verify duplicate export dates are rejected before writing.
def test_duplicate_export_dates_are_rejected_before_writing(tmp_path):
    # Build the file or folder path for path.
    path=tmp_path/'duplicate.csv'
    # Use a managed context for raises so exit handling runs automatically.
    with pytest.raises(ValueError,match='repeat'):
        # Run export csv with the supplied input.
        export_csv(path,[{'date':'2026-11-02','parent':'A'},{'date':'2026-11-02','parent':'B'}])
    # Verify that there is no exists before treating this check as successful.
    assert not path.exists()
