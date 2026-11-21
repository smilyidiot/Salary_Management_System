"""Shared SQL building blocks for resolving current salary in the database.

Both the directory listing and the analytics layer need "the most recent compensation
record per employee, annualized and converted to USD". Defining it once here keeps those
two features in agreement and keeps the heavy lifting (ranking, conversion, aggregation)
in SQL rather than Python — which is what lets it scale past 10k employees.
"""

from __future__ import annotations

from sqlalchemy import Subquery, case, func, select

from app.models import CompensationRecord
from app.reference import FX_TO_USD


def latest_comp_subquery() -> Subquery:
    """Subquery containing exactly the most recent compensation record per employee."""
    rn = func.row_number().over(
        partition_by=CompensationRecord.employee_id,
        order_by=(CompensationRecord.effective_from.desc(), CompensationRecord.id.desc()),
    ).label("rn")
    ranked = select(
        CompensationRecord.employee_id.label("eid"),
        CompensationRecord.base_amount.label("amount"),
        CompensationRecord.currency.label("currency"),
        CompensationRecord.pay_frequency.label("freq"),
        rn,
    ).subquery()
    return select(ranked).where(ranked.c.rn == 1).subquery()


def _freq_multiplier(latest: Subquery):
    """12 for monthly-quoted salaries, 1 for annual — annualizes the stored amount."""
    return case((latest.c.freq == "monthly", 12), else_=1)


def annual_local_expr(latest: Subquery):
    """Current salary annualized, still in its own currency."""
    return latest.c.amount * _freq_multiplier(latest)


def usd_expr(latest: Subquery):
    """Current salary annualized and converted to USD via the static FX table."""
    fx = case({code: float(rate) for code, rate in FX_TO_USD.items()}, value=latest.c.currency)
    return latest.c.amount * _freq_multiplier(latest) * fx
