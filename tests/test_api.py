"""Automated tests for the Student Records API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

NEW_STUDENT = {
    "name": "Priya Deshmukh",
    "roll_no": "CS104",
    "department": "Computer Engineering",
    "email": "priya.deshmukh@example.com",
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Every test gets its own empty database file, so tests never touch real data.
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("SEED_SAMPLE_DATA", "false")
    with TestClient(app) as test_client:
        yield test_client


def test_root_and_health(client):
    assert client.get("/").status_code == 200
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_add_student(client):
    response = client.post("/students", json=NEW_STUDENT)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == NEW_STUDENT["name"]


def test_view_all_students(client):
    assert client.get("/students").json() == []
    client.post("/students", json=NEW_STUDENT)
    client.post("/students", json={**NEW_STUDENT, "roll_no": "CS105"})
    response = client.get("/students")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_view_student_by_id(client):
    created = client.post("/students", json=NEW_STUDENT).json()
    response = client.get(f"/students/{created['id']}")
    assert response.status_code == 200
    assert response.json()["roll_no"] == "CS104"


def test_update_student(client):
    created = client.post("/students", json=NEW_STUDENT).json()
    updated_data = {**NEW_STUDENT, "department": "Information Technology"}
    response = client.put(f"/students/{created['id']}", json=updated_data)
    assert response.status_code == 200
    assert response.json()["department"] == "Information Technology"
    # The change should be saved in the database
    assert client.get(f"/students/{created['id']}").json()["department"] == "Information Technology"


def test_get_missing_student_returns_404(client):
    response = client.get("/students/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_missing_student_returns_404(client):
    response = client.put("/students/999", json=NEW_STUDENT)
    assert response.status_code == 404


def test_invalid_email_returns_422(client):
    response = client.post("/students", json={**NEW_STUDENT, "email": "not-an-email"})
    assert response.status_code == 422


def test_missing_field_returns_422(client):
    incomplete = {"name": "Priya Deshmukh", "roll_no": "CS104"}
    response = client.post("/students", json=incomplete)
    assert response.status_code == 422


def test_non_numeric_id_returns_422(client):
    response = client.get("/students/abc")
    assert response.status_code == 422


def test_duplicate_roll_no_returns_409(client):
    client.post("/students", json=NEW_STUDENT)
    response = client.post("/students", json=NEW_STUDENT)
    assert response.status_code == 409
