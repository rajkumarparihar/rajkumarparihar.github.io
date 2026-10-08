"""Career fair queue management API."""

import logging
import sqlite3
from contextlib import asynccontextmanager
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

import database

logger = logging.getLogger("career_fair")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with database.get_conn() as conn:
        database.init_db(conn)
        count = database.seed_students(conn)
    logger.info("Seeded %d students from %s", count, database.CSV_PATH)
    yield


app = FastAPI(title="Career Fair Queue Manager", version="1.0.0", lifespan=lifespan)


def get_db() -> Iterator[sqlite3.Connection]:
    with database.get_conn() as conn:
        yield conn


class EnqueueRequest(BaseModel):
    student_id: str = Field(alias="Student_ID", min_length=1)
    target_company: str = Field(alias="Target_Company", min_length=1)

    model_config = {"populate_by_name": True}

    @field_validator("student_id", "target_company")
    @classmethod
    def _strip_nonblank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class QueueEntry(BaseModel):
    position: int
    student_id: str
    company: str
    joined_at: str
    est_interaction_time_mins: float


class QueueResponse(BaseModel):
    company: str
    length: int
    queue: list[QueueEntry]


class WaitTimeResponse(BaseModel):
    company: str
    students_waiting: int
    estimated_wait_mins: float


def _normalize_company(company: str) -> str:
    company = company.strip()
    if not company:
        raise HTTPException(status_code=422, detail="Company must not be blank")
    return company


@app.post("/enqueue", response_model=QueueEntry, status_code=201)
def enqueue(req: EnqueueRequest, conn: sqlite3.Connection = Depends(get_db)):
    student = conn.execute(
        "SELECT est_interaction_time_mins FROM students WHERE student_id = ?",
        (req.student_id,),
    ).fetchone()
    if student is None:
        raise HTTPException(status_code=404, detail=f"Unknown student: {req.student_id}")

    try:
        cur = conn.execute(
            "INSERT INTO queues (student_id, company) VALUES (?, ?)",
            (req.student_id, req.target_company),
        )
    except sqlite3.IntegrityError:
        existing = conn.execute(
            "SELECT company FROM queues WHERE student_id = ?", (req.student_id,)
        ).fetchone()
        company = existing["company"] if existing else "another company"
        raise HTTPException(
            status_code=409,
            detail=f"Student {req.student_id} is already waiting in line for {company}",
        )

    row = conn.execute(
        "SELECT student_id, company, joined_at, id FROM queues WHERE id = ?",
        (cur.lastrowid,),
    ).fetchone()
    position = conn.execute(
        """
        SELECT COUNT(*) FROM queues
        WHERE company = ? AND (joined_at < ? OR (joined_at = ? AND id <= ?))
        """,
        (row["company"], row["joined_at"], row["joined_at"], row["id"]),
    ).fetchone()[0]
    return QueueEntry(
        position=position,
        student_id=row["student_id"],
        company=row["company"],
        joined_at=row["joined_at"],
        est_interaction_time_mins=student["est_interaction_time_mins"],
    )


@app.get("/queue/{company}", response_model=QueueResponse)
def get_queue(company: str, conn: sqlite3.Connection = Depends(get_db)):
    company = _normalize_company(company)
    rows = conn.execute(
        """
        SELECT q.student_id, q.company, q.joined_at, s.est_interaction_time_mins
        FROM queues q
        JOIN students s ON s.student_id = q.student_id
        WHERE q.company = ?
        ORDER BY q.joined_at, q.id
        """,
        (company,),
    ).fetchall()
    entries = [
        QueueEntry(position=i, **dict(r)) for i, r in enumerate(rows, start=1)
    ]
    return QueueResponse(company=company, length=len(entries), queue=entries)


@app.get("/wait-time/{company}", response_model=WaitTimeResponse)
def get_wait_time(company: str, conn: sqlite3.Connection = Depends(get_db)):
    company = _normalize_company(company)
    row = conn.execute(
        """
        SELECT COUNT(*) AS waiting,
               COALESCE(SUM(s.est_interaction_time_mins), 0) AS total_mins
        FROM queues q
        JOIN students s ON s.student_id = q.student_id
        WHERE q.company = ?
        """,
        (company,),
    ).fetchone()
    return WaitTimeResponse(
        company=company,
        students_waiting=row["waiting"],
        estimated_wait_mins=round(row["total_mins"], 2),
    )
