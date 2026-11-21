"""Unit tests for compensation resolution and salary-change validation.

These cover the core modeling decision — "current salary" is derived from the latest
effective-dated record — and the rules that protect history integrity.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.models import CompensationReason, PayFrequency
from app.schemas import CompensationCreate
from app.services.compensation import (
    CompensationError,
    annual_usd,
    annualize,
    current_record,
    record_salary_change,
)
from tests.factories import add_comp, make_employee


def test_current_record_picks_latest_effective_date():
    emp = make_employee()
    add_comp(emp, amount="80000", effective_from=date(2020, 1, 1), reason=CompensationReason.hire)
    add_comp(emp, amount="95000", effective_from=date(2023, 6, 1), reason=CompensationReason.raise_)
    add_comp(emp, amount="88000", effective_from=date(2021, 1, 1), reason=CompensationReason.adjustment)

    rec = current_record(emp)
    assert rec is not None
    assert rec.base_amount == Decimal("95000")
    assert rec.effective_from == date(2023, 6, 1)


def test_current_record_none_when_no_history():
    assert current_record(make_employee()) is None


def test_annualize_monthly_multiplies_by_twelve():
    emp = make_employee()
    rec = add_comp(emp, amount="10000", frequency=PayFrequency.monthly)
    assert annualize(rec) == Decimal("120000")


def test_annualize_annual_is_unchanged():
    emp = make_employee()
    rec = add_comp(emp, amount="120000", frequency=PayFrequency.annual)
    assert annualize(rec) == Decimal("120000")


def test_annual_usd_converts_monthly_inr():
    # 100000 INR/month -> 1,200,000 INR/year -> * 0.012 = 14,400 USD
    emp = make_employee(country="IN")
    rec = add_comp(emp, amount="100000", currency="INR", frequency=PayFrequency.monthly)
    assert annual_usd(rec) == Decimal("14400.000")


def test_record_salary_change_appends_to_history():
    emp = make_employee(hire_date=date(2019, 1, 1))
    add_comp(emp, amount="70000", effective_from=date(2019, 1, 1))

    data = CompensationCreate(
        base_amount=Decimal("90000"),
        currency="USD",
        pay_frequency=PayFrequency.annual,
        effective_from=date(2024, 1, 1),
        reason=CompensationReason.raise_,
    )
    record_salary_change(emp, data)

    assert len(emp.compensation_records) == 2
    assert current_record(emp).base_amount == Decimal("90000")


def test_record_salary_change_rejects_date_before_hire():
    emp = make_employee(hire_date=date(2022, 1, 1))
    data = CompensationCreate(
        base_amount=Decimal("90000"),
        currency="USD",
        pay_frequency=PayFrequency.annual,
        effective_from=date(2021, 1, 1),  # before hire
        reason=CompensationReason.adjustment,
    )
    with pytest.raises(CompensationError, match="hire date"):
        record_salary_change(emp, data)


def test_record_salary_change_rejects_unknown_currency():
    emp = make_employee(hire_date=date(2020, 1, 1))
    data = CompensationCreate(
        base_amount=Decimal("90000"),
        currency="XYZ",
        pay_frequency=PayFrequency.annual,
        effective_from=date(2021, 1, 1),
        reason=CompensationReason.raise_,
    )
    with pytest.raises(CompensationError, match="unknown currency"):
        record_salary_change(emp, data)
