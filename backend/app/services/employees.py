"""Employee query and mutation logic.

The directory list is the performance-sensitive path at 10k rows. It resolves each
employee's current salary with a single window-function join (one row per employee) rather
than per-employee queries, and computes/sorts the USD figure in SQL so paging and ordering
stay in the database.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models import Employee, EmploymentStatus
from app.schemas import CompensationCreate, EmployeeCreate, EmployeeUpdate
from app.services.compensation import record_salary_change
from app.services.salary_sql import annual_local_expr, latest_comp_subquery, usd_expr

SORT_FIELDS = {"full_name", "country", "department", "level", "hire_date", "current_salary_usd"}


@dataclass
class EmployeeFilters:
    q: str | None = None
    country: str | None = None
    department: str | None = None
    employment_status: EmploymentStatus | None = None
    sort: str = "full_name"
    order: str = "asc"
    page: int = 1
    page_size: int = 25


@dataclass
class EmployeeRow:
    """An employee plus their resolved current compensation (one directory row)."""

    employee: Employee
    current_salary: Decimal | None
    currency: str | None
    current_salary_usd: Decimal | None


def _apply_filters(stmt: Select, latest, filters: EmployeeFilters) -> Select:
    if filters.q:
        like = f"%{filters.q}%"
        stmt = stmt.where(
            or_(
                Employee.full_name.ilike(like),
                Employee.employee_code.ilike(like),
                Employee.email.ilike(like),
            )
        )
    if filters.country:
        stmt = stmt.where(Employee.country == filters.country)
    if filters.department:
        stmt = stmt.where(Employee.department == filters.department)
    if filters.employment_status:
        stmt = stmt.where(Employee.employment_status == filters.employment_status)
    return stmt


def _rows_from(result) -> list[EmployeeRow]:
    rows: list[EmployeeRow] = []
    for emp, annual_local, currency, usd in result:
        rows.append(
            EmployeeRow(
                employee=emp,
                current_salary=annual_local,
                currency=currency,
                current_salary_usd=(round(Decimal(str(usd)), 2) if usd is not None else None),
            )
        )
    return rows


def _base_select(latest):
    annual_local = annual_local_expr(latest).label("annual_local")
    usd = usd_expr(latest).label("salary_usd")
    return (
        select(Employee, annual_local, latest.c.currency, usd)
        .join(latest, latest.c.eid == Employee.id, isouter=True),
        usd,
    )


def list_employees(session: Session, filters: EmployeeFilters) -> tuple[list[EmployeeRow], int]:
    latest = latest_comp_subquery()
    stmt, usd_label = _base_select(latest)
    stmt = _apply_filters(stmt, latest, filters)

    total = session.scalar(
        _apply_filters(select(func.count()).select_from(Employee), latest, filters)
    )

    sort_field = filters.sort if filters.sort in SORT_FIELDS else "full_name"
    if sort_field == "current_salary_usd":
        order_col = usd_label
    else:
        order_col = getattr(Employee, sort_field)
    order_col = order_col.desc() if filters.order == "desc" else order_col.asc()
    # Stable tiebreaker so pagination is deterministic.
    stmt = stmt.order_by(order_col, Employee.id.asc())

    stmt = stmt.limit(filters.page_size).offset((filters.page - 1) * filters.page_size)
    rows = _rows_from(session.execute(stmt).all())
    return rows, int(total or 0)


def iter_all_for_export(session: Session, filters: EmployeeFilters) -> list[EmployeeRow]:
    """Same filtered set as the list, but every matching row (no pagination) for CSV export."""
    latest = latest_comp_subquery()
    stmt, _ = _base_select(latest)
    stmt = _apply_filters(stmt, latest, filters).order_by(Employee.full_name.asc(), Employee.id.asc())
    return _rows_from(session.execute(stmt).all())


def get_employee(session: Session, employee_id: int) -> Employee | None:
    return session.get(Employee, employee_id)


def next_employee_code(session: Session) -> str:
    """Generate the next sequential employee code, e.g. E10001."""
    max_code = session.scalar(select(func.max(Employee.employee_code)))
    next_num = (int(max_code[1:]) + 1) if max_code else 1
    return f"E{next_num:05d}"


def create_employee(session: Session, data: EmployeeCreate) -> Employee:
    if data.manager_id is not None and session.get(Employee, data.manager_id) is None:
        raise ValueError(f"manager_id {data.manager_id} does not exist")

    employee = Employee(
        employee_code=next_employee_code(session),
        full_name=data.full_name,
        email=str(data.email),
        country=data.country.upper(),
        department=data.department,
        job_title=data.job_title,
        level=data.level,
        manager_id=data.manager_id,
        hire_date=data.hire_date,
        employment_status=data.employment_status,
    )
    session.add(employee)
    record_salary_change(employee, data.initial_compensation)
    session.commit()
    session.refresh(employee)
    return employee


def update_employee(session: Session, employee: Employee, data: EmployeeUpdate) -> Employee:
    updates = data.model_dump(exclude_unset=True)

    if "manager_id" in updates and updates["manager_id"] is not None:
        if updates["manager_id"] == employee.id:
            raise ValueError("an employee cannot be their own manager")
        if session.get(Employee, updates["manager_id"]) is None:
            raise ValueError(f"manager_id {updates['manager_id']} does not exist")

    for field, value in updates.items():
        if field == "email" and value is not None:
            value = str(value)
        if field == "country" and value is not None:
            value = value.upper()
        setattr(employee, field, value)

    session.commit()
    session.refresh(employee)
    return employee


def add_compensation(session: Session, employee: Employee, data: CompensationCreate) -> Employee:
    record_salary_change(employee, data)
    session.commit()
    session.refresh(employee)
    return employee
