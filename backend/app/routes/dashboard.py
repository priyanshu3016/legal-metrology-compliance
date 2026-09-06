"""
APIRouter: Dashboard

Endpoints
---------
GET /api/v1/dashboard/summary              - Get overall dashboard statistics
GET /api/v1/dashboard/recent-inspections   - List 10 most recent inspections
GET /api/v1/dashboard/violations           - Get violation counts by severity
GET /api/v1/dashboard/compliance-trend     - Get monthly compliance trend
"""

from __future__ import annotations

from typing import Annotated
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.inspection import Inspection
from app.models.violation import Violation
from app.schemas.dashboard import (
    ComplianceTrend,
    DashboardSummary,
    RecentInspection,
    ViolationSummary,
)

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)

DBSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get overall dashboard statistics",
)
def get_dashboard_summary(db: DBSession) -> DashboardSummary:
    # Inspection stats
    total_inspections = db.query(Inspection).count()
    compliant = db.query(Inspection).filter(Inspection.status == "compliant").count()
    non_compliant = db.query(Inspection).filter(Inspection.status == "non_compliant").count()
    pending = db.query(Inspection).filter(Inspection.status == "pending").count()

    compliance_rate = 0.0
    if total_inspections > 0:
        compliance_rate = (compliant / total_inspections) * 100.0

    # Violation stats
    total_violations = db.query(Violation).count()
    critical = db.query(Violation).filter(Violation.severity == "critical").count()
    high = db.query(Violation).filter(Violation.severity == "high").count()
    medium = db.query(Violation).filter(Violation.severity == "medium").count()
    low = db.query(Violation).filter(Violation.severity == "low").count()

    return DashboardSummary(
        total_inspections=total_inspections,
        compliant_inspections=compliant,
        non_compliant_inspections=non_compliant,
        pending_inspections=pending,
        total_violations=total_violations,
        critical_violations=critical,
        high_violations=high,
        medium_violations=medium,
        low_violations=low,
        compliance_rate=round(compliance_rate, 2),
    )


@router.get(
    "/recent-inspections",
    response_model=list[RecentInspection],
    summary="List recent inspections",
)
def get_recent_inspections(db: DBSession) -> list[RecentInspection]:
    inspections = (
        db.query(Inspection)
        .options(
            joinedload(Inspection.product),
            joinedload(Inspection.inspector),
        )
        .order_by(Inspection.created_at.desc())
        .limit(10)
        .all()
    )

    result = []
    for insp in inspections:
        prod_name = insp.product.name if insp.product else None
        insp_name = insp.inspector.name if insp.inspector else None
        result.append(
            RecentInspection(
                id=insp.id,
                reference_number=insp.reference_number,
                product_name=prod_name,
                location=insp.location,
                status=insp.status,
                compliance_score=insp.compliance_score,
                created_at=insp.created_at,
                inspector_name=insp_name,
            )
        )
    return result


@router.get(
    "/violations",
    response_model=ViolationSummary,
    summary="Get violation summary by severity",
)
def get_violation_summary(db: DBSession) -> ViolationSummary:
    rows = (
        db.query(Violation.severity, func.count(Violation.id))
        .group_by(Violation.severity)
        .all()
    )
    counts = {severity: count for severity, count in rows}
    return ViolationSummary(
        critical=counts.get("critical", 0),
        high=counts.get("high", 0),
        medium=counts.get("medium", 0),
        low=counts.get("low", 0),
    )


@router.get(
    "/compliance-trend",
    response_model=list[ComplianceTrend],
    summary="Get monthly compliance trend",
)
def get_compliance_trend(db: DBSession) -> list[ComplianceTrend]:
    # Group by YYYY-MM
    # SQLite strftime works on created_at
    rows = (
        db.query(
            func.strftime("%Y-%m", Inspection.created_at).label("month"),
            func.count(Inspection.id).label("total"),
            func.sum(
                case((Inspection.status == "compliant", 1), else_=0)
            ).label("compliant_count"),
        )
        .group_by("month")
        .order_by("month")
        .all()
    )

    trend = []
    for row in rows:
        month = row.month
        if not month:
            continue
        total = row.total or 0
        comp_count = row.compliant_count or 0
        rate = (comp_count / total * 100.0) if total > 0 else 0.0
        trend.append(
            ComplianceTrend(
                month=month,
                total_inspections=total,
                compliant_inspections=comp_count,
                compliance_rate=round(rate, 2),
            )
        )
    return trend
