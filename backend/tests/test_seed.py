"""Tests for the seed script: data invariants and determinism.

The seed must be safe to build analytics and demos on, so it should always produce a
well-formed population, and must be reproducible run to run for a given seed.
"""

from __future__ import annotations

import hashlib

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import CompensationRecord, Employee
from app.seed import generate


def _fresh_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _dataset_hash(session) -> str:
    h = hashlib.sha256()
    for emp in session.query(Employee).order_by(Employee.id).all():
        h.update(f"{emp.employee_code}|{emp.full_name}|{emp.country}|{emp.level}|{emp.manager_id}".encode())
        for r in sorted(emp.compensation_records, key=lambda r: r.effective_from):
            # Format money with fixed precision so a DB round-trip (50600.00) and an
            # in-memory value (50600) hash identically — they are the same amount.
            h.update(f"{r.base_amount:.2f}|{r.currency}|{r.effective_from}|{r.reason.value}".encode())
    return h.hexdigest()


def test_generates_requested_count():
    session = _fresh_session()
    n = generate(session, count=100, seed=42)
    assert n == 100
    assert session.query(Employee).count() == 100


def test_every_employee_has_compensation():
    session = _fresh_session()
    generate(session, count=100, seed=42)
    without = session.query(Employee).filter(~Employee.compensation_records.any()).count()
    assert without == 0


def test_all_amounts_positive():
    session = _fresh_session()
    generate(session, count=100, seed=42)
    nonpositive = session.query(CompensationRecord).filter(CompensationRecord.base_amount <= 0).count()
    assert nonpositive == 0


def test_single_org_head_and_no_self_management():
    session = _fresh_session()
    generate(session, count=200, seed=42)
    heads = session.query(Employee).filter(Employee.manager_id.is_(None)).count()
    assert heads == 1
    self_managed = session.query(Employee).filter(Employee.manager_id == Employee.id).count()
    assert self_managed == 0


def test_deterministic_for_same_seed():
    a = _fresh_session()
    generate(a, count=150, seed=42)
    b = _fresh_session()
    generate(b, count=150, seed=42)
    assert _dataset_hash(a) == _dataset_hash(b)


def test_different_seed_produces_different_data():
    a = _fresh_session()
    generate(a, count=150, seed=42)
    b = _fresh_session()
    generate(b, count=150, seed=99)
    assert _dataset_hash(a) != _dataset_hash(b)
