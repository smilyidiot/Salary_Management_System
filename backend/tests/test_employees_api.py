"""API tests for the employee endpoints, driven through the FastAPI app.

Covers the directory (pagination, search, filtering), detail + 404, creation with the
required starting compensation, recording a raise, validation failures, updates, and CSV
export — the full HR workflow surface.
"""

from __future__ import annotations

import pytest

from app.seed import generate


@pytest.fixture
def seeded(session_factory):
    """Seed a small deterministic dataset into the test database."""
    session = session_factory()
    generate(session, count=40, seed=1)
    session.close()


NEW_EMPLOYEE = {
    "full_name": "Dana Hire",
    "email": "dana.hire@acme.co",
    "country": "US",
    "department": "Engineering",
    "job_title": "Software Engineer",
    "level": "L3",
    "manager_id": None,
    "hire_date": "2024-01-15",
    "employment_status": "active",
    "initial_compensation": {
        "base_amount": "95000.00",
        "currency": "USD",
        "pay_frequency": "annual",
        "effective_from": "2024-01-15",
        "reason": "hire",
    },
}


def test_list_is_paginated(client, seeded):
    resp = client.get("/api/employees", params={"page_size": 10, "page": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 40
    assert body["pages"] == 4
    assert len(body["items"]) == 10
    # Current salary is resolved for every row.
    assert all(item["current_salary_usd"] is not None for item in body["items"])


def test_list_filter_by_country(client, seeded):
    resp = client.get("/api/employees", params={"country": "IN", "page_size": 100})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(item["country"] == "IN" for item in items)


def test_list_search_matches_code(client, seeded):
    resp = client.get("/api/employees", params={"q": "E00001"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(item["employee_code"] == "E00001" for item in items)


def test_get_detail_and_404(client):
    created = client.post("/api/employees", json=NEW_EMPLOYEE).json()
    ok = client.get(f"/api/employees/{created['id']}")
    assert ok.status_code == 200
    assert ok.json()["full_name"] == "Dana Hire"
    assert len(ok.json()["compensation_records"]) == 1

    assert client.get("/api/employees/99999999").status_code == 404


def test_create_generates_code_and_current_salary(client):
    resp = client.post("/api/employees", json=NEW_EMPLOYEE)
    assert resp.status_code == 201
    body = resp.json()
    assert body["employee_code"] == "E00001"
    # Money is serialized as a precision-safe string, not a float.
    assert body["current_salary_usd"] == "95000.00"


def test_create_rejects_nonexistent_manager(client):
    payload = {**NEW_EMPLOYEE, "manager_id": 123456}
    resp = client.post("/api/employees", json=payload)
    assert resp.status_code == 400
    assert "manager_id" in resp.json()["detail"]


def test_record_raise_updates_current_salary(client):
    emp = client.post("/api/employees", json=NEW_EMPLOYEE).json()
    resp = client.post(
        f"/api/employees/{emp['id']}/compensation",
        json={
            "base_amount": "115000.00",
            "currency": "USD",
            "pay_frequency": "annual",
            "effective_from": "2025-06-01",
            "reason": "raise",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["current_salary_usd"] == "115000.00"
    assert len(body["compensation_records"]) == 2


def test_record_raise_before_hire_is_rejected(client):
    emp = client.post("/api/employees", json=NEW_EMPLOYEE).json()
    resp = client.post(
        f"/api/employees/{emp['id']}/compensation",
        json={
            "base_amount": "80000.00",
            "currency": "USD",
            "pay_frequency": "annual",
            "effective_from": "2000-01-01",
            "reason": "adjustment",
        },
    )
    assert resp.status_code == 400
    assert "hire date" in resp.json()["detail"]


def test_patch_updates_fields(client):
    emp = client.post("/api/employees", json=NEW_EMPLOYEE).json()
    resp = client.patch(
        f"/api/employees/{emp['id']}",
        json={"department": "Product", "employment_status": "on_leave"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["department"] == "Product"
    assert body["employment_status"] == "on_leave"


def test_create_validation_error_on_bad_payload(client):
    bad = {**NEW_EMPLOYEE}
    del bad["email"]
    resp = client.post("/api/employees", json=bad)
    assert resp.status_code == 422  # Pydantic validation


def test_csv_export(client, seeded):
    resp = client.get("/api/employees/export.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    lines = resp.text.strip().splitlines()
    assert lines[0].startswith("employee_code,full_name,email")
    assert len(lines) == 41  # header + 40 rows
