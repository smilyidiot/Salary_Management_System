"""Pydantic request/response schemas.

Kept separate from ORM models so the API contract can evolve independently of the
database shape.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import CompensationReason, EmploymentStatus, PayFrequency

# ---------------------------------------------------------------------------
# Compensation
# ---------------------------------------------------------------------------


class CompensationCreate(BaseModel):
    base_amount: Decimal = Field(gt=0, description="Amount in the given currency (per pay period)")
    currency: str = Field(min_length=3, max_length=3)
    pay_frequency: PayFrequency = PayFrequency.annual
    effective_from: date
    reason: CompensationReason


class CompensationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    base_amount: Decimal
    currency: str
    pay_frequency: PayFrequency
    effective_from: date
    reason: CompensationReason


# ---------------------------------------------------------------------------
# Employee
# ---------------------------------------------------------------------------


class EmployeeBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    country: str = Field(min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    department: str = Field(min_length=1, max_length=60)
    job_title: str = Field(min_length=1, max_length=80)
    level: str = Field(min_length=1, max_length=16)
    manager_id: int | None = None
    hire_date: date
    employment_status: EmploymentStatus = EmploymentStatus.active


class EmployeeCreate(EmployeeBase):
    # A new employee must be created with their starting compensation so there is never an
    # employee without salary history.
    initial_compensation: CompensationCreate


class EmployeeUpdate(BaseModel):
    """All fields optional — only provided fields are changed."""

    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    country: str | None = Field(default=None, min_length=2, max_length=2)
    department: str | None = Field(default=None, min_length=1, max_length=60)
    job_title: str | None = Field(default=None, min_length=1, max_length=80)
    level: str | None = Field(default=None, min_length=1, max_length=16)
    manager_id: int | None = None
    hire_date: date | None = None
    employment_status: EmploymentStatus | None = None


class ManagerRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_code: str
    full_name: str


class EmployeeListItem(BaseModel):
    """Row in the directory list, including the resolved current salary."""

    id: int
    employee_code: str
    full_name: str
    email: str
    country: str
    department: str
    job_title: str
    level: str
    employment_status: EmploymentStatus
    manager_id: int | None
    # Current (most recent) compensation, annualized into local currency, plus USD equivalent.
    current_salary: Decimal | None
    currency: str | None
    current_salary_usd: Decimal | None


class EmployeeDetail(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_code: str
    manager: ManagerRef | None = None
    compensation_records: list[CompensationOut] = []
    current_salary: Decimal | None = None
    currency: str | None = None
    current_salary_usd: Decimal | None = None


class PaginatedEmployees(BaseModel):
    items: list[EmployeeListItem]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


class GroupStat(BaseModel):
    """Pay statistics for one country or department. All money in USD."""

    key: str
    label: str
    headcount: int
    avg_salary_usd: Decimal
    median_salary_usd: Decimal
    total_payroll_usd: Decimal


class StatusCount(BaseModel):
    status: EmploymentStatus
    count: int


class DistributionBucket(BaseModel):
    label: str
    min_usd: int
    max_usd: int | None  # open-ended for the top band
    count: int


class AnalyticsSummary(BaseModel):
    """Headline numbers. Pay figures cover the current workforce (excludes terminated)."""

    total_headcount: int
    workforce_headcount: int  # active + on_leave, i.e. the pay population
    total_payroll_usd: Decimal
    average_salary_usd: Decimal
    median_salary_usd: Decimal
    by_status: list[StatusCount]
