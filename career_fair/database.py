"""SQLite setup and CSV seeding for the career fair queue system."""

import csv
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("CAREER_FAIR_DB", BASE_DIR / "career_fair.db"))
CSV_PATH = Path(os.environ.get("CAREER_FAIR_CSV", BASE_DIR / "career_fair_1000.csv"))

ID_COLUMN = "Student_ID"
TIME_COLUMN = "Est_Interaction_Time_Mins"

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id                TEXT PRIMARY KEY,
    est_interaction_time_mins REAL NOT NULL CHECK (est_interaction_time_mins >= 0),
    extra                     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS queues (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL UNIQUE REFERENCES students(student_id),
    company    TEXT NOT NULL COLLATE NOCASE,
    joined_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_queues_company_joined
    ON queues (company, joined_at, id);
"""


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_conn(db_path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a connection; commit on success, roll back on error, always close."""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def _read_students(csv_path: Path) -> list[tuple[str, float, str]]:
    """Parse the CSV into (student_id, est_minutes, extra_json) rows.

    Columns other than Student_ID / Est_Interaction_Time_Mins are preserved as JSON
    in the `extra` column. Duplicate IDs keep the last occurrence.
    """
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = [(name or "").strip() for name in (reader.fieldnames or [])]
        missing = {ID_COLUMN, TIME_COLUMN} - set(fields)
        if missing:
            raise ValueError(
                f"{csv_path} is missing required column(s): {', '.join(sorted(missing))}"
            )

        rows: dict[str, tuple[str, float, str]] = {}
        for line_no, raw in enumerate(reader, start=2):
            row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
            student_id = row.pop(ID_COLUMN)
            if not student_id:
                raise ValueError(f"{csv_path}:{line_no}: empty {ID_COLUMN}")
            try:
                minutes = float(row.pop(TIME_COLUMN))
            except ValueError as exc:
                raise ValueError(
                    f"{csv_path}:{line_no}: invalid {TIME_COLUMN} for {student_id}"
                ) from exc
            if minutes < 0:
                raise ValueError(f"{csv_path}:{line_no}: negative {TIME_COLUMN}")
            rows[student_id] = (student_id, minutes, json.dumps(row))
        return list(rows.values())


def seed_students(conn: sqlite3.Connection, csv_path: Path | str | None = None) -> int:
    """Upsert every attendee from the CSV. Safe to run on every startup.

    An upsert (rather than delete + insert) keeps existing queue rows valid.
    Returns the number of CSV rows processed.
    """
    path = Path(csv_path or CSV_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Attendee CSV not found: {path}")
    rows = _read_students(path)
    conn.executemany(
        """
        INSERT INTO students (student_id, est_interaction_time_mins, extra)
        VALUES (?, ?, ?)
        ON CONFLICT(student_id) DO UPDATE SET
            est_interaction_time_mins = excluded.est_interaction_time_mins,
            extra = excluded.extra
        """,
        rows,
    )
    return len(rows)
