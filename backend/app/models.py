"""ORM models.

Two tables:

* ``employees`` — one row per person.
* ``compensation_records`` — effective-dated salary history; "current salary" is the
  record with the latest ``effective_from`` for an employee. Salary changes are appended,
  never updated, so the history is an immutable audit trail.
"""

from __future__ import annotations

import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class EmploymentStatus(str, enum.Enum):
    active = "active"
    on_leave = "on_leave"
    terminated = "terminated"


class PayFrequency(str, enum.Enum):
    annual = "annual"
    monthly = "monthly"


class CompensationReason(str, enum.Enum):
    hire = "hire"
    raise_ = "raise"
    promotion = "promotion"
    adjustment = "adjustment"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(160), unique=True)
    country: Mapped[str] = mapped_column(String(2), index=True)  # ISO 3166-1 alpha-2
    department: Mapped[str] = mapped_column(String(60), index=True)
    job_title: Mapped[str] = mapped_column(String(80))
    level: Mapped[str] = mapped_column(String(16))
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), index=True)
    hire_date: Mapped[date] = mapped_column(Date)
    employment_status: Mapped[EmploymentStatus] = mapped_column(
        SAEnum(EmploymentStatus, native_enum=False, length=16),
        default=EmploymentStatus.active,
        index=True,
    )

    compensation_records: Mapped[list[CompensationRecord]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="CompensationRecord.effective_from",
    )
    manager: Mapped[Employee | None] = relationship(remote_side="Employee.id")


class CompensationRecord(Base):
    __tablename__ = "compensation_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True
    )
    # Money as exact Decimal (14,2) — never float.
    base_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3))  # ISO 4217
    pay_frequency: Mapped[PayFrequency] = mapped_column(
        SAEnum(PayFrequency, native_enum=False, length=16),
        default=PayFrequency.annual,
    )
    effective_from: Mapped[date] = mapped_column(Date)
    reason: Mapped[CompensationReason] = mapped_column(
        SAEnum(CompensationReason, native_enum=False, length=16)
    )

    employee: Mapped[Employee] = relationship(back_populates="compensation_records")

    __table_args__ = (
        # Primary access path: resolve an employee's current/most-recent record quickly.
        Index("ix_comp_employee_effective", "employee_id", "effective_from"),
    )
