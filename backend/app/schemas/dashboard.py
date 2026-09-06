"""
Pydantic v2 schemas for the Dashboard API.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DashboardSummary(BaseModel):
    """Overall summary statistics for the dashboard."""
    total_inspections: int
    compliant_inspections: int
    non_compliant_inspections: int
    pending_inspections: int
    total_violations: int
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int
    compliance_rate: float


class RecentInspection(BaseModel):
    """Schema for a single recent inspection displayed on the dashboard."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_number: str
    product_name: str | None = None
    location: str | None = None
    status: str
    compliance_score: float | None = None
    created_at: datetime
    inspector_name: str | None = None


class ViolationSummary(BaseModel):
    """Summary of violations grouped by severity."""
    critical: int
    high: int
    medium: int
    low: int


class ComplianceTrend(BaseModel):
    """Monthly compliance trend data point."""
    month: str  # Format: "YYYY-MM"
    total_inspections: int
    compliant_inspections: int
    compliance_rate: float
