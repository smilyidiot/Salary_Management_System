"""Unit tests for the pay-analytics aggregations.

Built on a tiny, fully known dataset so every average, median, total, and bucket count can
be asserted exactly — including USD conversion of a non-USD market and exclusion of
terminated employees from pay figures.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.models import EmploymentStatus, PayFrequency
from app.services import analytics
from tests.factories import add_comp, make_employee


@pytest.fixture
def dataset(db_session):
    """5 active employees (3 US, 2 GB in GBP) plus 1 terminated (should be excluded)."""
    specs = [
        ("E1", "US", "USD", "60000", EmploymentStatus.active),
        ("E2", "US", "USD", "80000", EmploymentStatus.active),
        ("E3", "US", "USD", "100000", EmploymentStatus.active),
        ("E4", "GB", "GBP", "100000", EmploymentStatus.active),  # -> 127,000 USD
        ("E5", "GB", "GBP", "50000", EmploymentStatus.active),   # ->  63,500 USD
        ("E6", "US", "USD", "999999", EmploymentStatus.terminated),  # excluded from pay
    ]
    for code, country, currency, amount, status in specs:
        emp = make_employee(db_session, code=code, country=country, status=status,
                            email=f"{code}@acme.co")
        add_comp(emp, amount=amount, currency=currency, effective_from=date(2020, 1, 1),
                 frequency=PayFrequency.annual)
    db_session.commit()
    return db_session


def test_summary_excludes_terminated_from_pay(dataset):
    s = analytics.summary(dataset)
    assert s["total_headcount"] == 6
    assert s["workforce_headcount"] == 5
    # workforce USD salaries: 60k, 80k, 100k, 127k, 63.5k
    assert s["total_payroll_usd"] == Decimal("430500.00")
    assert s["average_salary_usd"] == Decimal("86100.00")
    assert s["median_salary_usd"] == Decimal("80000.00")


def test_summary_status_breakdown(dataset):
    s = analytics.summary(dataset)
    by_status = {item["status"]: item["count"] for item in s["by_status"]}
    assert by_status[EmploymentStatus.active] == 5
    assert by_status[EmploymentStatus.terminated] == 1


def test_by_country_values_and_order(dataset):
    rows = analytics.group_breakdown(dataset, "country")
    # Sorted by headcount desc: US (3) before GB (2).
    assert [r["key"] for r in rows] == ["US", "GB"]

    us = rows[0]
    assert us["label"] == "United States"
    assert us["headcount"] == 3
    assert us["avg_salary_usd"] == Decimal("80000.00")
    assert us["median_salary_usd"] == Decimal("80000.00")
    assert us["total_payroll_usd"] == Decimal("240000.00")

    gb = rows[1]
    assert gb["headcount"] == 2
    assert gb["avg_salary_usd"] == Decimal("95250.00")  # (127000 + 63500) / 2
    assert gb["total_payroll_usd"] == Decimal("190500.00")


def test_distribution_buckets(dataset):
    buckets = {b["label"]: b["count"] for b in analytics.distribution(dataset)}
    assert buckets["< $50k"] == 0
    assert buckets["$50k–$75k"] == 2      # 60000, 63500
    assert buckets["$75k–$100k"] == 1     # 80000
    assert buckets["$100k–$150k"] == 2    # 100000, 127000
    assert buckets["$150k–$200k"] == 0
    assert buckets["$200k+"] == 0
    assert sum(b["count"] for b in analytics.distribution(dataset)) == 5
