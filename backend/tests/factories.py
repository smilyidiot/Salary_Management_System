"""Tiny builders for constructing known employees and compensation in tests.

Using explicit, hand-built data (rather than the random seed script) lets analytics and
compensation tests assert exact expected numbers.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models import (
    CompensationRecord,
    CompensationReason,
    Employee,
    EmploymentStatus,
    PayFrequency,
)


def make_employee(
    session=None,
    *,
    code: str = "E00001",
    full_name: str = "Test Person",
    email: str | None = None,
    country: str = "US",
    department: str = "Engineering",
    job_title: str = "Software Engineer",
    level: str = "L3",
    manager_id: int | None = None,
    hire_date: date = date(2020, 1, 1),
    status: EmploymentStatus = EmploymentStatus.active,
) -> Employee:
    employee = Employee(
        employee_code=code,
        full_name=full_name,
        email=email or f"{code.lower()}@acme.co",
        country=country,
        department=department,
        job_title=job_title,
        level=level,
        manager_id=manager_id,
        hire_date=hire_date,
        employment_status=status,
    )
    if session is not None:
        session.add(employee)
    return employee


def add_comp(
    employee: Employee,
    *,
    amount: str,
    currency: str = "USD",
    effective_from: date = date(2020, 1, 1),
    frequency: PayFrequency = PayFrequency.annual,
    reason: CompensationReason = CompensationReason.hire,
) -> CompensationRecord:
    record = CompensationRecord(
        base_amount=Decimal(amount),
        currency=currency,
        pay_frequency=frequency,
        effective_from=effective_from,
        reason=reason,
    )
    employee.compensation_records.append(record)
    return record
