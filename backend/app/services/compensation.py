"""Compensation logic: current-salary resolution, annualization, and recording changes.

"Current salary" is always derived from the record with the latest ``effective_from`` —
there is no stored current-salary field to drift out of sync. Salary changes are appended,
never updated, preserving an immutable history.
"""

from __future__ import annotations

from decimal import Decimal

from app.models import CompensationRecord, Employee, PayFrequency
from app.reference import to_usd
from app.schemas import CompensationCreate


class CompensationError(ValueError):
    """Raised when a salary change is invalid (surfaced as HTTP 400 by the router)."""


def current_record(employee: Employee) -> CompensationRecord | None:
    """Most recent compensation record for an employee (by effective date, then id)."""
    if not employee.compensation_records:
        return None
    return max(employee.compensation_records, key=lambda r: (r.effective_from, r.id))


def annualize(record: CompensationRecord) -> Decimal:
    """Amount expressed as an annual figure in its own currency."""
    multiplier = Decimal("12") if record.pay_frequency == PayFrequency.monthly else Decimal("1")
    return record.base_amount * multiplier


def annual_usd(record: CompensationRecord) -> Decimal:
    """Annualized amount converted to USD via the static FX table."""
    return to_usd(annualize(record), record.currency)


def record_salary_change(employee: Employee, data: CompensationCreate) -> CompensationRecord:
    """Validate and append a new compensation record to an employee's history.

    Does not commit — the caller owns the transaction.
    """
    if data.effective_from < employee.hire_date:
        raise CompensationError("effective_from cannot be before the employee's hire date")
    if data.currency.upper() not in _known_currencies():
        raise CompensationError(f"unknown currency '{data.currency}'")

    record = CompensationRecord(
        base_amount=data.base_amount,
        currency=data.currency.upper(),
        pay_frequency=data.pay_frequency,
        effective_from=data.effective_from,
        reason=data.reason,
    )
    employee.compensation_records.append(record)
    return record


def _known_currencies() -> set[str]:
    from app.reference import FX_TO_USD

    return set(FX_TO_USD.keys())
