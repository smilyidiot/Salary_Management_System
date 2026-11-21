"""Pay-analytics endpoints backing the HR dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AnalyticsSummary, DistributionBucket, GroupStat
from app.services import analytics as svc

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def summary(db: Session = Depends(get_db)):
    return svc.summary(db)


@router.get("/by-country", response_model=list[GroupStat])
def by_country(db: Session = Depends(get_db)):
    return svc.group_breakdown(db, "country")


@router.get("/by-department", response_model=list[GroupStat])
def by_department(db: Session = Depends(get_db)):
    return svc.group_breakdown(db, "department")


@router.get("/distribution", response_model=list[DistributionBucket])
def distribution(db: Session = Depends(get_db)):
    return svc.distribution(db)
