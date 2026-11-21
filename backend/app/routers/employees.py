"""Employee directory, detail, create/update, salary-change, and CSV export endpoints."""

from __future__ import annotations

import csv
import io
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Employee, EmploymentStatus
from app.schemas import (
    CompensationCreate,
    EmployeeCreate,
    EmployeeDetail,
    EmployeeListItem,
    EmployeeUpdate,
    PaginatedEmployees,
)
from app.services import employees as svc
from app.services.compensation import CompensationError, annual_usd, annualize, current_record

router = APIRouter(prefix="/api/employees", tags=["employees"])


# --- response builders ------------------------------------------------------


def _to_list_item(row: svc.EmployeeRow) -> EmployeeListItem:
    e = row.employee
    return EmployeeListItem(
        id=e.id,
        employee_code=e.employee_code,
        full_name=e.full_name,
        email=e.email,
        country=e.country,
        department=e.department,
        job_title=e.job_title,
        level=e.level,
        employment_status=e.employment_status,
        manager_id=e.manager_id,
        current_salary=row.current_salary,
        currency=row.currency,
        current_salary_usd=row.current_salary_usd,
    )


def _to_detail(employee: Employee) -> EmployeeDetail:
    detail = EmployeeDetail.model_validate(employee)
    rec = current_record(employee)
    if rec is not None:
        detail.current_salary = annualize(rec)
        detail.currency = rec.currency
        detail.current_salary_usd = round(annual_usd(rec), 2)
    return detail


def _get_or_404(db: Session, employee_id: int) -> Employee:
    employee = svc.get_employee(db, employee_id)
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


# --- endpoints --------------------------------------------------------------


@router.get("", response_model=PaginatedEmployees)
def list_employees(
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, description="Search name, employee code, or email"),
    country: str | None = None,
    department: str | None = None,
    employment_status: EmploymentStatus | None = None,
    sort: str = Query(default="full_name"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
):
    filters = svc.EmployeeFilters(
        q=q,
        country=country,
        department=department,
        employment_status=employment_status,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    rows, total = svc.list_employees(db, filters)
    return PaginatedEmployees(
        items=[_to_list_item(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if page_size else 0,
    )


@router.get("/export.csv")
def export_csv(
    db: Session = Depends(get_db),
    q: str | None = None,
    country: str | None = None,
    department: str | None = None,
    employment_status: EmploymentStatus | None = None,
):
    filters = svc.EmployeeFilters(
        q=q, country=country, department=department, employment_status=employment_status
    )
    rows = svc.iter_all_for_export(db, filters)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "employee_code", "full_name", "email", "country", "department", "job_title",
            "level", "employment_status", "current_salary", "currency", "current_salary_usd",
        ]
    )
    for r in rows:
        e = r.employee
        writer.writerow(
            [
                e.employee_code, e.full_name, e.email, e.country, e.department, e.job_title,
                e.level, e.employment_status.value,
                r.current_salary if r.current_salary is not None else "",
                r.currency or "",
                r.current_salary_usd if r.current_salary_usd is not None else "",
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"},
    )


@router.get("/{employee_id}", response_model=EmployeeDetail)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    return _to_detail(_get_or_404(db, employee_id))


@router.post("", response_model=EmployeeDetail, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        employee = svc.create_employee(db, payload)
    except (ValueError, CompensationError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_detail(employee)


@router.patch("/{employee_id}", response_model=EmployeeDetail)
def update_employee(employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = _get_or_404(db, employee_id)
    try:
        employee = svc.update_employee(db, employee, payload)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_detail(employee)


@router.post(
    "/{employee_id}/compensation",
    response_model=EmployeeDetail,
    status_code=status.HTTP_201_CREATED,
)
def add_compensation(employee_id: int, payload: CompensationCreate, db: Session = Depends(get_db)):
    employee = _get_or_404(db, employee_id)
    try:
        employee = svc.add_compensation(db, employee, payload)
    except CompensationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_detail(employee)
