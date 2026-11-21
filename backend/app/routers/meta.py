"""Reference-data endpoint that feeds the frontend's filter and form dropdowns."""

from __future__ import annotations

from fastapi import APIRouter

from app.models import CompensationReason, EmploymentStatus, PayFrequency
from app.reference import COUNTRIES, DEPARTMENTS, LEVELS

router = APIRouter(prefix="/api/reference", tags=["reference"])


@router.get("")
def reference() -> dict:
    """Static option lists so the UI and API share one source of truth for valid values."""
    return {
        "countries": [
            {"code": c.code, "name": c.name, "currency": c.currency} for c in COUNTRIES.values()
        ],
        "departments": DEPARTMENTS,
        "levels": LEVELS,
        "employment_statuses": [s.value for s in EmploymentStatus],
        "pay_frequencies": [f.value for f in PayFrequency],
        "compensation_reasons": [r.value for r in CompensationReason],
    }
