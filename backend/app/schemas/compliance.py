"""
Pydantic v2 schemas for the Compliance API.

Used by:
  POST /api/v1/inspections/{id}/compliance  -> run compliance check
  GET  /api/v1/inspections/{id}/compliance  -> get last compliance result
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Per-check result (mirrors CheckResult dataclass)
# ---------------------------------------------------------------------------

class CheckResultSchema(BaseModel):
    """Schema for a single rule-check result."""

    field_name: str
    rule_code: str
    status: str          # "PASS" | "FAIL"
    message: str
    severity: str        # "LOW" | "MEDIUM" | "HIGH"


# ---------------------------------------------------------------------------
# Violation summary (stored rows)
# ---------------------------------------------------------------------------

class ViolationRead(BaseModel):
    """Read schema for a Violation ORM row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    field_name: str | None = None
    severity: str
    description: str
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Full compliance result response
# ---------------------------------------------------------------------------

class ComplianceResponse(BaseModel):
    """
    Response for POST and GET /compliance endpoints.

    Contains:
    - overall_status : COMPLIANT or NON_COMPLIANT
    - score          : 0-100, rounded to 2 dp
    - check results  : one entry per rule
    - violations     : only the FAIL entries persisted to the DB
    """

    inspection_id: int
    overall_status: str
    score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    checks: list[CheckResultSchema]
    violations: list[ViolationRead]
