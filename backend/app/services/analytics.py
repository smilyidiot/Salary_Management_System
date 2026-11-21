"""Pay analytics — the reporting that answers "how does the org pay people?".

Counts, averages, and totals are computed as SQL ``GROUP BY`` aggregates over a
window-function join, so they stay fast at 10k+ employees. Medians are the one figure
SQLite has no native function for, so they are computed in Python from a single ordered
pull per dimension (documented trade-off; see docs/DECISIONS.md).

Pay figures cover the current workforce — employees who are ``active`` or ``on_leave``.
Terminated employees are excluded from salary aggregates but still counted in headcount
breakdowns.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Employee, EmploymentStatus
from app.reference import COUNTRIES
from app.services.salary_sql import latest_comp_subquery, usd_expr

# Employees counted in pay aggregates (currently employed).
WORKFORCE_STATUSES = (EmploymentStatus.active, EmploymentStatus.on_leave)

# USD salary bands for the distribution chart: (label, min inclusive, max exclusive or None).
DISTRIBUTION_BANDS: list[tuple[str, int, int | None]] = [
    ("< $50k", 0, 50_000),
    ("$50k–$75k", 50_000, 75_000),
    ("$75k–$100k", 75_000, 100_000),
    ("$100k–$150k", 100_000, 150_000),
    ("$150k–$200k", 150_000, 200_000),
    ("$200k+", 200_000, None),
]


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _workforce_filter(stmt):
    return stmt.where(Employee.employment_status.in_(WORKFORCE_STATUSES))


def _group_stats(session: Session, group_col) -> list[dict]:
    """count / avg / total payroll (USD) per group, via a single SQL GROUP BY."""
    latest = latest_comp_subquery()
    usd = usd_expr(latest)
    stmt = _workforce_filter(
        select(group_col, func.count(), func.avg(usd), func.sum(usd))
        .select_from(Employee)
        .join(latest, latest.c.eid == Employee.id)
    ).group_by(group_col)

    out = []
    for key, count, avg_usd, total_usd in session.execute(stmt).all():
        out.append(
            {
                "key": key,
                "headcount": int(count),
                "avg_salary_usd": _money(avg_usd),
                "total_payroll_usd": _money(total_usd),
            }
        )
    return out


def _group_medians(session: Session, group_col) -> dict[str, Decimal]:
    """Median USD salary per group (computed in Python; SQLite has no median function)."""
    latest = latest_comp_subquery()
    usd = usd_expr(latest)
    stmt = _workforce_filter(
        select(group_col, usd).select_from(Employee).join(latest, latest.c.eid == Employee.id)
    )
    buckets: dict[str, list[float]] = defaultdict(list)
    for key, value in session.execute(stmt).all():
        buckets[key].append(float(value))
    return {key: _money(statistics.median(vals)) for key, vals in buckets.items() if vals}


def _labelled(key: str, group: str) -> str:
    if group == "country":
        country = COUNTRIES.get(key)
        return country.name if country else key
    return key


def group_breakdown(session: Session, group: str) -> list[dict]:
    """Per-country or per-department pay stats, sorted by headcount descending."""
    group_col = Employee.country if group == "country" else Employee.department
    stats = _group_stats(session, group_col)
    medians = _group_medians(session, group_col)

    for row in stats:
        row["label"] = _labelled(row["key"], group)
        row["median_salary_usd"] = medians.get(row["key"], Decimal("0.00"))

    stats.sort(key=lambda r: r["headcount"], reverse=True)
    return stats


def summary(session: Session) -> dict:
    latest = latest_comp_subquery()
    usd = usd_expr(latest)

    # Headcount by status (all employees).
    status_rows = session.execute(
        select(Employee.employment_status, func.count()).group_by(Employee.employment_status)
    ).all()
    by_status = [{"status": status, "count": int(count)} for status, count in status_rows]
    total_headcount = sum(item["count"] for item in by_status)

    # Pay aggregates over the current workforce.
    workforce_count, avg_usd, total_usd = session.execute(
        _workforce_filter(
            select(func.count(), func.avg(usd), func.sum(usd))
            .select_from(Employee)
            .join(latest, latest.c.eid == Employee.id)
        )
    ).one()

    median_values = [
        float(v)
        for (v,) in session.execute(
            _workforce_filter(
                select(usd).select_from(Employee).join(latest, latest.c.eid == Employee.id)
            )
        ).all()
    ]
    median_usd = _money(statistics.median(median_values)) if median_values else Decimal("0.00")

    return {
        "total_headcount": total_headcount,
        "workforce_headcount": int(workforce_count or 0),
        "total_payroll_usd": _money(total_usd),
        "average_salary_usd": _money(avg_usd),
        "median_salary_usd": median_usd,
        "by_status": by_status,
    }


def distribution(session: Session) -> list[dict]:
    """Headcount per USD salary band, for the distribution chart."""
    latest = latest_comp_subquery()
    usd = usd_expr(latest)

    # Map each salary to a band index in SQL, then group.
    whens = []
    for idx, (_, _lo, hi) in enumerate(DISTRIBUTION_BANDS):
        if hi is not None:
            whens.append((usd < hi, idx))
    band_idx = case(*whens, else_=len(DISTRIBUTION_BANDS) - 1).label("band")

    stmt = _workforce_filter(
        select(band_idx, func.count()).select_from(Employee).join(latest, latest.c.eid == Employee.id)
    ).group_by(band_idx)

    counts = {int(idx): int(count) for idx, count in session.execute(stmt).all()}
    result = []
    for idx, (label, lo, hi) in enumerate(DISTRIBUTION_BANDS):
        result.append({"label": label, "min_usd": lo, "max_usd": hi, "count": counts.get(idx, 0)})
    return result
