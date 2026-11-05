"""Local persistence and CSV output, separated from UI dialogs.

SQLite parameters bind values instead of concatenating SQL, preserving quotes in
record names and avoiding SQL injection. Each write uses a transaction context:
success commits, while an exception rolls back. The GUI owns overwrite/delete
confirmation; these functions perform only the requested local data operation.
"""
# Load csv for use in this module.
import csv
# Bring in contextmanager from contextlib.
from contextlib import contextmanager
# Load json for use in this module.
import json
# Load sqlite3 for use in this module.
import sqlite3
# Bring in date, datetime, timezone from datetime.
from datetime import date, datetime, timezone
# Bring in Path from pathlib.
from pathlib import Path
# Bring in ReviewSession from session.
from .session import ReviewSession
# Bring in Schedule from core.
from .core import Schedule

# Set schema version to 1.
SCHEMA_VERSION = 1


# Group the state and behavior for the store.
class Store:
    def __init__(self, path: Path):
        # Create the output directory before writing files into it.
        path.parent.mkdir(parents=True, exist_ok=True)
        # Keep the database path so each operation can open its own short-lived connection.
        self.path = path
        # Use a managed database connection. Successful writes commit and failed writes roll back.
        with self.connect() as db:
            # Run this database statement with the supplied parameters.
            db.execute('''CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, version INTEGER NOT NULL,
                payload TEXT NOT NULL, created_at TEXT NOT NULL)''')

    # Manage a short-lived SQLite connection and its transaction.
    @contextmanager
    def connect(self):
        # Opening short-lived connections avoids sharing one SQLite handle
        # across worker threads. The with-block handles each transaction.
        connection = sqlite3.connect(self.path)
        # Attempt this operation so its failure can be handled below.
        try:
            # Use a managed context for connection so exit handling runs automatically.
            with connection:
                yield connection
        finally:
            # A sqlite connection's own with-block commits/rolls back but does
            # not close it. Explicit close prevents file handles accumulating.
            connection.close()

    def save(self, name: str, session: ReviewSession) -> int:
        # Handle the case where there is no approved or schedule is no value.
        if not session.approved or session.schedule is None:
            # Stop with a clear error explaining only approved rules can be saved.
            raise ValueError('Only approved rules can be saved')
        # Handle the case where there is no strip.
        if not name.strip():
            # Stop with a clear error explaining enter a record name.
            raise ValueError('Enter a record name')
        # Serialize the rules alongside their source pages and document identity so the record can be reviewed after reopening.
        payload = {'rules': session.schedule.model_dump(mode='json'),
                   'pages': session.pages, 'source_name': session.source_name,
                   'source_hash': session.source_hash, 'approved_at_save': True}
        # Use a managed database connection. Successful writes commit and failed writes roll back.
        with self.connect() as db:
            # Bind values through placeholders so the record name and source text remain data.
            cursor = db.execute('INSERT INTO schedules(name,version,payload,created_at) VALUES(?,?,?,?)',
                (name.strip(), SCHEMA_VERSION, json.dumps(payload), datetime.now(timezone.utc).isoformat()))
            # Return lastrowid to the caller.
            return cursor.lastrowid

    def list_records(self):
        # Use a managed database connection. Successful writes commit and failed writes roll back.
        with self.connect() as db:
            # Return fetchall to the caller.
            return db.execute('SELECT id,name,created_at FROM schedules ORDER BY id DESC').fetchall()

    def load(self, record_id: int) -> ReviewSession:
        # Use a managed database connection. Successful writes commit and failed writes roll back.
        with self.connect() as db:
            # Set row from fetchone.
            row = db.execute('SELECT version,payload FROM schedules WHERE id=?',(record_id,)).fetchone()
        # Handle the case where row is no value.
        if row is None:
            # Stop with a clear error explaining saved record no longer exists.
            raise ValueError('Saved record no longer exists')
        # Reject incompatible stored layouts before reading fields from the payload.
        if row[0] != SCHEMA_VERSION:
            # Stop with a clear error explaining unsupported saved-record schema version.
            raise ValueError('Unsupported saved-record schema version')
        # Set data from loads.
        data = json.loads(row[1])
        # Restore the record into a fresh session, which starts without approval.
        session = ReviewSession()
        # Use replace document on session.
        session.replace_document(data['pages'],data['source_name'],data['source_hash'])
        # Use propose on session.
        session.propose(Schedule.model_validate(data['rules']))
        # Historical approval is retained as provenance, not trusted as a fresh
        # user decision. Loading always requires review again before generation.
        return session

    def delete(self, record_id: int):
        # Use a managed database connection. Successful writes commit and failed writes roll back.
        with self.connect() as db:
            # Run this database statement with the supplied parameters.
            db.execute('DELETE FROM schedules WHERE id=?',(record_id,))


# Validate every date and owner before opening the output file.
def export_csv(path: Path, rows: list[dict], overwrite=False):
    # Handle the case where there is no rows.
    if not rows:
        # Stop with a clear error explaining generate calendar rows before exporting.
        raise ValueError('Generate calendar rows before exporting')
    # Validate the entire batch before opening the destination. A malformed
    # later row must not truncate an existing export or leave a partial new one.
    # ISO dates and A/B labels also prevent arbitrary spreadsheet formulas from
    # entering these two exported columns through an unexpected caller.
    # Track dates during validation so each exported overnight has only one row.
    seen_dates=set()
    # Process each row from rows.
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'date','parent'}:
            # Stop with a clear error explaining each export row must contain only date and
            # parent.
            raise ValueError('Each export row must contain only date and parent')
        # Handle the case where there is no isinstance.
        if not isinstance(row['date'],str):
            # Stop with a clear error explaining export dates must be iso date strings.
            raise ValueError('Export dates must be ISO date strings')
        # Attempt this operation so its failure can be handled below.
        try:
            # Set parsed from fromisoformat.
            parsed=date.fromisoformat(row['date'])
        # Handle value error raised by the attempted operation.
        except ValueError as error:
            # Stop with a clear error explaining export dates must be valid iso dates.
            raise ValueError('Export dates must be valid ISO dates') from error
        # Handle the case where isoformat differs from date field or parent field is absent from
        # 'A', 'B'.
        if parsed.isoformat()!=row['date'] or row['parent'] not in ('A','B'):
            # Stop with a clear error explaining export rows require iso dates and parent a/b
            # labels.
            raise ValueError('Export rows require ISO dates and Parent A/B labels')
        # Handle the case where date field is in seen dates.
        if row['date'] in seen_dates:
            # Stop with a clear error explaining export rows must not repeat a date.
            raise ValueError('Export rows must not repeat a date')
        # Use add on seen dates.
        seen_dates.add(row['date'])
    # Exclusive creation protects an existing file even if UI state changes
    # between the existence check and this write. Only explicit overwrite uses w.
    with path.open('w' if overwrite else 'x', newline='', encoding='utf-8') as stream:
        # Write the two columns in a predictable order for spreadsheet imports.
        writer = csv.DictWriter(stream, fieldnames=['date','parent'])
        # Use writeheader on writer.
        writer.writeheader()
        # Use writerows on writer.
        writer.writerows(rows)
