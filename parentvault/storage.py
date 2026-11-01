"""Local persistence and CSV output, separated from UI dialogs.

SQLite parameters bind values instead of concatenating SQL, preserving quotes in
record names and avoiding SQL injection. Each write uses a transaction context:
success commits, while an exception rolls back. The GUI owns overwrite/delete
confirmation; these functions perform only the requested local data operation.
"""
import csv
from contextlib import contextmanager
import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from .session import ReviewSession
from .core import Schedule

SCHEMA_VERSION = 1


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, version INTEGER NOT NULL,
                payload TEXT NOT NULL, created_at TEXT NOT NULL)''')

    @contextmanager
    def connect(self):
        # Opening short-lived connections avoids sharing one SQLite handle
        # across worker threads. The with-block handles each transaction.
        connection = sqlite3.connect(self.path)
        try:
            with connection:
                yield connection
        finally:
            # A sqlite connection's own with-block commits/rolls back but does
            # not close it. Explicit close prevents file handles accumulating.
            connection.close()

    def save(self, name: str, session: ReviewSession) -> int:
        if not session.approved or session.schedule is None:
            raise ValueError('Only approved rules can be saved')
        if not name.strip():
            raise ValueError('Enter a record name')
        payload = {'rules': session.schedule.model_dump(mode='json'),
                   'pages': session.pages, 'source_name': session.source_name,
                   'source_hash': session.source_hash, 'approved_at_save': True}
        with self.connect() as db:
            cursor = db.execute('INSERT INTO schedules(name,version,payload,created_at) VALUES(?,?,?,?)',
                (name.strip(), SCHEMA_VERSION, json.dumps(payload), datetime.now(timezone.utc).isoformat()))
            return cursor.lastrowid

    def list_records(self):
        with self.connect() as db:
            return db.execute('SELECT id,name,created_at FROM schedules ORDER BY id DESC').fetchall()

    def load(self, record_id: int) -> ReviewSession:
        with self.connect() as db:
            row = db.execute('SELECT version,payload FROM schedules WHERE id=?',(record_id,)).fetchone()
        if row is None:
            raise ValueError('Saved record no longer exists')
        if row[0] != SCHEMA_VERSION:
            raise ValueError('Unsupported saved-record schema version')
        data = json.loads(row[1])
        session = ReviewSession()
        session.replace_document(data['pages'],data['source_name'],data['source_hash'])
        session.propose(Schedule.model_validate(data['rules']))
        # Historical approval is retained as provenance, not trusted as a fresh
        # user decision. Loading always requires review again before generation.
        return session

    def delete(self, record_id: int):
        with self.connect() as db:
            db.execute('DELETE FROM schedules WHERE id=?',(record_id,))


def export_csv(path: Path, rows: list[dict], overwrite=False):
    if not rows:
        raise ValueError('Generate calendar rows before exporting')
    # Validate the entire batch before opening the destination. A malformed
    # later row must not truncate an existing export or leave a partial new one.
    # ISO dates and A/B labels also prevent arbitrary spreadsheet formulas from
    # entering these two exported columns through an unexpected caller.
    seen_dates=set()
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'date','parent'}:
            raise ValueError('Each export row must contain only date and parent')
        if not isinstance(row['date'],str):
            raise ValueError('Export dates must be ISO date strings')
        try:
            parsed=date.fromisoformat(row['date'])
        except ValueError as error:
            raise ValueError('Export dates must be valid ISO dates') from error
        if parsed.isoformat()!=row['date'] or row['parent'] not in ('A','B'):
            raise ValueError('Export rows require ISO dates and Parent A/B labels')
        if row['date'] in seen_dates:
            raise ValueError('Export rows must not repeat a date')
        seen_dates.add(row['date'])
    # Exclusive creation protects an existing file even if UI state changes
    # between the existence check and this write. Only explicit overwrite uses w.
    with path.open('w' if overwrite else 'x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['date','parent'])
        writer.writeheader()
        writer.writerows(rows)
