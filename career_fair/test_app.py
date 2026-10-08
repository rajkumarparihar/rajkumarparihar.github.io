import sqlite3

import pytest
from fastapi.testclient import TestClient

import database
import generate_sample_csv


@pytest.fixture()
def client(tmp_path, monkeypatch):
    csv_path = tmp_path / "career_fair_1000.csv"
    generate_sample_csv.generate(csv_path)
    monkeypatch.setattr(database, "CSV_PATH", csv_path)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    import main

    with TestClient(main.app) as c:
        yield c


def minutes(client, sid):
    with database.get_conn() as conn:
        return conn.execute(
            "SELECT est_interaction_time_mins FROM students WHERE student_id=?", (sid,)
        ).fetchone()[0]


def test_seeds_1000_students(client):
    with database.get_conn() as conn:
        assert conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 1000


def test_reseed_is_idempotent_and_keeps_queue(client):
    client.post("/enqueue", json={"Student_ID": "S0001", "Target_Company": "Acme"})
    with database.get_conn() as conn:
        database.seed_students(conn)
        assert conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 1000
        assert conn.execute("SELECT COUNT(*) FROM queues").fetchone()[0] == 1


def test_enqueue_queue_and_wait_time(client):
    for sid in ["S0001", "S0002", "S0003"]:
        r = client.post("/enqueue", json={"Student_ID": sid, "Target_Company": "Acme"})
        assert r.status_code == 201
    client.post("/enqueue", json={"Student_ID": "S0004", "Target_Company": "Globex"})

    q = client.get("/queue/Acme").json()
    assert q["length"] == 3
    assert [e["student_id"] for e in q["queue"]] == ["S0001", "S0002", "S0003"]
    assert [e["position"] for e in q["queue"]] == [1, 2, 3]

    expected = sum(minutes(client, s) for s in ["S0001", "S0002", "S0003"])
    w = client.get("/wait-time/Acme").json()
    assert w["students_waiting"] == 3
    assert w["estimated_wait_mins"] == expected
    assert client.get("/wait-time/acme").json()["estimated_wait_mins"] == expected


def test_empty_queue(client):
    assert client.get("/queue/Nobody").json() == {"company": "Nobody", "length": 0, "queue": []}
    assert client.get("/wait-time/Nobody").json()["estimated_wait_mins"] == 0


def test_unknown_student_404(client):
    r = client.post("/enqueue", json={"Student_ID": "NOPE", "Target_Company": "Acme"})
    assert r.status_code == 404


def test_duplicate_enqueue_409(client):
    client.post("/enqueue", json={"Student_ID": "S0001", "Target_Company": "Acme"})
    r = client.post("/enqueue", json={"Student_ID": "S0001", "Target_Company": "Globex"})
    assert r.status_code == 409


def test_validation_422(client):
    assert client.post("/enqueue", json={"Student_ID": "S0001"}).status_code == 422
    r = client.post("/enqueue", json={"Student_ID": "S0001", "Target_Company": "  "})
    assert r.status_code == 422
