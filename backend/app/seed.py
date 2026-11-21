"""Deterministic seed script.

Generates a realistic, multi-country employee population with effective-dated salary
history. Deterministic: a fixed RNG seed makes every run identical, so data, tests, and
demos are reproducible.

Usage:
    python -m app.seed                 # 10,000 employees, seed 42 (drops existing data)
    python -m app.seed --count 500     # smaller set (used by tests)
    python -m app.seed --seed 7
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models import CompensationRecord, CompensationReason, Employee, EmploymentStatus, PayFrequency
from app.reference import COUNTRIES, DEPARTMENTS, FX_TO_USD, LEVEL_BASE_USD, LEVELS, title_for

# Name pools — small but enough for varied, readable data.
FIRST_NAMES = [
    "Alex", "Maria", "Chen", "Priya", "James", "Sofia", "Liam", "Aisha", "Noah", "Yuki",
    "Carlos", "Fatima", "Oliver", "Ananya", "Lucas", "Mei", "Ethan", "Zara", "Daniel", "Nina",
    "Mateo", "Ingrid", "Omar", "Elena", "Hiro", "Grace", "Ivan", "Leila", "Thomas", "Rosa",
]
LAST_NAMES = [
    "Smith", "Garcia", "Wang", "Patel", "Johnson", "Silva", "Mueller", "Kim", "Brown", "Tanaka",
    "Nguyen", "Rossi", "Lee", "Khan", "Dubois", "Santos", "Jones", "Costa", "Novak", "Haddad",
    "Walker", "Ali", "Fischer", "Reyes", "Yamamoto", "Clark", "Petrov", "Sharma", "Andersson", "Mendez",
]

# Relative weighting so the org is pyramid-shaped (many juniors, few seniors).
LEVEL_WEIGHTS = [28, 24, 18, 14, 9, 5, 2]  # L1..L7
MANAGER_LEVELS = {"L5", "L6", "L7"}
STATUS_WEIGHTS = [(EmploymentStatus.active, 90), (EmploymentStatus.on_leave, 5), (EmploymentStatus.terminated, 5)]

TODAY = date(2026, 11, 21)


def _round_amount(amount: Decimal, currency: str) -> Decimal:
    """Round to a market-sensible step: large-denomination currencies to the nearest 1000."""
    step = Decimal("1000") if currency in ("INR",) else Decimal("100")
    return (amount / step).quantize(Decimal("1")) * step


def _weighted_choice(rng: random.Random, items: list, weights: list[int]):
    return rng.choices(items, weights=weights, k=1)[0]


def _build_history(
    rng: random.Random, country_code: str, level: str, hire_date: date
) -> list[CompensationRecord]:
    """Create 1-3 effective-dated records whose latest value sits in the level's band."""
    country = COUNTRIES[country_code]
    rate = FX_TO_USD[country.currency]

    # Target current salary in USD, then convert to local currency.
    target_usd = Decimal(LEVEL_BASE_USD[level]) * Decimal(str(country.cost_of_living))
    target_usd *= Decimal(str(round(rng.uniform(0.85, 1.15), 3)))
    target_local_annual = target_usd / rate
    if country.monthly_pay:
        target_current = target_local_annual / Decimal("12")
        freq = PayFrequency.monthly
    else:
        target_current = target_local_annual
        freq = PayFrequency.annual

    # Effective dates first: first at hire, each raise 12-30 months later, never in the
    # future. Deciding dates up front means we only derive amounts for raises that fit, so
    # the latest record always lands at the target band (no undershoot for recent hires).
    intended_records = _weighted_choice(rng, [1, 2, 3], [25, 45, 30])
    dates = [hire_date]
    for _ in range(intended_records - 1):
        gap_months = rng.randint(12, 30)
        next_date = dates[-1] + timedelta(days=int(gap_months * 30.4))
        if next_date >= TODAY:
            break
        dates.append(next_date)

    # One growth factor per actual raise; start back-computed so the final record == target.
    growths = [Decimal(str(round(rng.uniform(1.05, 1.18), 3))) for _ in range(len(dates) - 1)]
    total_growth = Decimal("1")
    for g in growths:
        total_growth *= g
    start_amount = target_current / total_growth

    records: list[CompensationRecord] = []
    amount = start_amount
    for i, eff in enumerate(dates):
        if i == 0:
            reason = CompensationReason.hire
        else:
            amount *= growths[i - 1]
            reason = CompensationReason.promotion if growths[i - 1] > Decimal("1.13") else CompensationReason.raise_
        records.append(
            CompensationRecord(
                base_amount=_round_amount(amount, country.currency),
                currency=country.currency,
                pay_frequency=freq,
                effective_from=eff,
                reason=reason,
            )
        )
    return records


def generate(session: Session, count: int, seed: int) -> int:
    rng = random.Random(seed)
    country_codes = list(COUNTRIES.keys())

    employees: list[Employee] = []
    for i in range(1, count + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        level = _weighted_choice(rng, LEVELS, LEVEL_WEIGHTS)
        country_code = rng.choice(country_codes)
        department = rng.choice(DEPARTMENTS)
        status = _weighted_choice(
            rng, [s for s, _ in STATUS_WEIGHTS], [w for _, w in STATUS_WEIGHTS]
        )
        hire_date = TODAY - timedelta(days=rng.randint(60, 365 * 11))

        emp = Employee(
            employee_code=f"E{i:05d}",
            full_name=f"{first} {last}",
            email=f"{first}.{last}.{i}@acme.co".lower(),
            country=country_code,
            department=department,
            job_title=title_for(department, level),
            level=level,
            hire_date=hire_date,
            employment_status=status,
        )
        emp.compensation_records = _build_history(rng, country_code, level, hire_date)
        employees.append(emp)

    session.add_all(employees)
    session.flush()  # assign ids before wiring up the management hierarchy

    _assign_managers(rng, employees)
    session.commit()
    return len(employees)


def _assign_managers(rng: random.Random, employees: list[Employee]) -> None:
    """Give each employee a manager of strictly higher level (acyclic), same country when possible."""
    level_rank = {lvl: idx for idx, lvl in enumerate(LEVELS)}
    managers = [e for e in employees if e.level in MANAGER_LEVELS]
    if not managers:
        return

    # The single most senior manager is the org head (no manager).
    ceo = max(managers, key=lambda e: level_rank[e.level])
    by_country: dict[str, list[Employee]] = {}
    for m in managers:
        by_country.setdefault(m.country, []).append(m)

    for e in employees:
        if e is ceo:
            continue
        pool = [m for m in by_country.get(e.country, []) if level_rank[m.level] > level_rank[e.level]]
        if not pool:
            pool = [m for m in managers if level_rank[m.level] > level_rank[e.level]]
        e.manager_id = rng.choice(pool).id if pool else ceo.id


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the salary database.")
    parser.add_argument("--count", type=int, default=10_000, help="number of employees")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility")
    args = parser.parse_args()

    # Fresh, deterministic dataset every run.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        n = generate(session, count=args.count, seed=args.seed)
        comp_count = session.query(CompensationRecord).count()

    print(f"Seeded {n} employees and {comp_count} compensation records (seed={args.seed}).")


if __name__ == "__main__":
    main()
