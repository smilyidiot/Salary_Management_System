"""Static reference data shared by the seed script and the analytics layer.

Keeping currencies, FX rates, and salary bands in one place means seeded data and the
USD-normalization used in reporting always agree. FX rates are static and illustrative
(see docs/DECISIONS.md) — this keeps the app deterministic and offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Country:
    code: str  # ISO 3166-1 alpha-2
    name: str
    currency: str  # ISO 4217
    cost_of_living: float  # salary multiplier relative to the US
    monthly_pay: bool  # whether salaries are quoted monthly in this market


COUNTRIES: dict[str, Country] = {
    "US": Country("US", "United States", "USD", 1.00, monthly_pay=False),
    "GB": Country("GB", "United Kingdom", "GBP", 0.95, monthly_pay=False),
    "DE": Country("DE", "Germany", "EUR", 0.90, monthly_pay=False),
    "CA": Country("CA", "Canada", "CAD", 0.85, monthly_pay=False),
    "AU": Country("AU", "Australia", "AUD", 0.90, monthly_pay=False),
    "SG": Country("SG", "Singapore", "SGD", 0.95, monthly_pay=False),
    "IN": Country("IN", "India", "INR", 0.35, monthly_pay=True),
    "BR": Country("BR", "Brazil", "BRL", 0.50, monthly_pay=True),
}

# USD value of one unit of each currency (amount_local * rate = USD). Illustrative, static.
FX_TO_USD: dict[str, Decimal] = {
    "USD": Decimal("1.00"),
    "GBP": Decimal("1.27"),
    "EUR": Decimal("1.08"),
    "CAD": Decimal("0.73"),
    "AUD": Decimal("0.66"),
    "SGD": Decimal("0.74"),
    "INR": Decimal("0.012"),
    "BRL": Decimal("0.20"),
}

DEPARTMENTS: list[str] = [
    "Engineering",
    "Sales",
    "Marketing",
    "Finance",
    "Human Resources",
    "Operations",
    "Customer Support",
    "Product",
]

# Career levels and the midpoint annual base salary (in USD) for each.
LEVELS: list[str] = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]

LEVEL_BASE_USD: dict[str, int] = {
    "L1": 50_000,
    "L2": 65_000,
    "L3": 85_000,
    "L4": 110_000,
    "L5": 140_000,
    "L6": 180_000,
    "L7": 240_000,
}

# Job title by department and seniority bucket (junior L1-L3, mid L4-L5, senior L6-L7).
JOB_TITLES: dict[str, tuple[str, str, str]] = {
    "Engineering": ("Software Engineer", "Senior Software Engineer", "Engineering Manager"),
    "Sales": ("Sales Representative", "Account Executive", "Sales Director"),
    "Marketing": ("Marketing Associate", "Marketing Manager", "Head of Marketing"),
    "Finance": ("Financial Analyst", "Finance Manager", "Finance Director"),
    "Human Resources": ("HR Associate", "HR Manager", "Head of People"),
    "Operations": ("Operations Analyst", "Operations Manager", "Operations Director"),
    "Customer Support": ("Support Specialist", "Support Lead", "Support Director"),
    "Product": ("Product Analyst", "Product Manager", "Head of Product"),
}


def title_for(department: str, level: str) -> str:
    junior, mid, senior = JOB_TITLES[department]
    if level in ("L1", "L2", "L3"):
        return junior
    if level in ("L4", "L5"):
        return mid
    return senior


def to_usd(amount: Decimal, currency: str) -> Decimal:
    """Convert a local-currency amount to USD using the static FX table."""
    return amount * FX_TO_USD[currency]
