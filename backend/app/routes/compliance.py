"""
APIRouter: Compliance

Prefix : /api/v1/inspections/{inspection_id}/compliance
Tags   : ["Compliance"]

Architecture
------------
  Declaration rows (stored by Step 6)
          |
  run_compliance()  <-- pure deterministic Python, no AI
          |
  Violation rows  +  inspection.compliance_score  +  inspection.status
          |
  ComplianceResponse returned to caller

Endpoints
---------
POST /   Run the deterministic compliance rules engine against the
         stored declarations for an inspection.
         Persists violations (upsert: delete-then-insert to avoid duplicates).
         Updates inspection.compliance_score and inspection.status.

GET  /   Return the latest stored compliance result for an inspection
         (reads violations table + rebuilds check summary from rules).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.declaration import Declaration
from app.models.inspection import Inspection
from app.models.violation import Violation
from app.schemas.compliance import (
    CheckResultSchema,
    ComplianceResponse,
    ViolationRead,
)
from app.services.compliance import RULES, CheckResult, run_compliance

router = APIRouter(
    prefix="/api/v1/inspections/{inspection_id}/compliance",
    tags=["Compliance"],
)

DBSession = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_inspection_or_404(inspection_id: int, db: Session) -> Inspection:
    obj = db.get(Inspection, inspection_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with id={inspection_id} not found.",
        )
    return obj


def _build_response(
    inspection_id: int,
    inspection: Inspection,
    checks: list[CheckResult],
    violations: list[Violation],
    total_checks: int,
    passed_checks: int,
    failed_checks: int,
    overall_status: str,
    score: float,
) -> ComplianceResponse:
    return ComplianceResponse(
        inspection_id=inspection_id,
        overall_status=overall_status,
        score=score,
        total_checks=total_checks,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        checks=[
            CheckResultSchema(
                field_name=c.field_name,
                rule_code=c.rule_code,
                status=c.status,
                message=c.message,
                severity=c.severity,
            )
            for c in checks
        ],
        violations=[ViolationRead.model_validate(v) for v in violations],
    )


# ---------------------------------------------------------------------------
# POST /api/v1/inspections/{inspection_id}/compliance  — Run engine
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ComplianceResponse,
    summary="Run compliance rules engine",
    description=(
        "Execute all deterministic Legal Metrology compliance rules against "
        "the stored Declaration records for this inspection. "
        "Violations are **upserted** (previous violations for this inspection are "
        "replaced so repeated calls never create duplicates). "
        "Updates `inspection.compliance_score` and `inspection.status`. "
        "Does **not** use AI or LLM for any compliance decision."
    ),
)
def run_compliance_check(
    inspection_id: int,
    db: DBSession,
) -> ComplianceResponse:
    inspection = _get_inspection_or_404(inspection_id, db)

    # --- Load declarations ---
    decl_rows = (
        db.query(Declaration)
        .filter(Declaration.inspection_id == inspection_id)
        .all()
    )
    declarations: dict[str, str | None] = {d.field_name: d.value for d in decl_rows}

    # --- Run pure-Python rules engine ---
    result = run_compliance(declarations)

    # --- Upsert violations: delete existing, then insert new FAILs ---
    # This guarantees no duplicate violations on repeated calls.
    db.query(Violation).filter(Violation.inspection_id == inspection_id).delete(
        synchronize_session=False
    )

    new_violations: list[Violation] = []
    for check in result.checks:
        if check.status == "FAIL":
            v = Violation(
                inspection_id=inspection_id,
                rule_id=None,           # no Rule rows seeded yet
                field_name=check.field_name,
                severity=check.severity.lower(),   # model stores lowercase
                description=f"[{check.rule_code}] {check.message}",
                confidence=None,
                status="open",
            )
            db.add(v)
            new_violations.append(v)

    # --- Update inspection ---
    inspection.compliance_score = result.score
    inspection.status = (
        "compliant" if result.overall_status == "COMPLIANT" else "non_compliant"
    )

    db.commit()
    for v in new_violations:
        db.refresh(v)
    db.refresh(inspection)

    return _build_response(
        inspection_id=inspection_id,
        inspection=inspection,
        checks=result.checks,
        violations=new_violations,
        total_checks=result.total_checks,
        passed_checks=result.passed_checks,
        failed_checks=result.failed_checks,
        overall_status=result.overall_status,
        score=result.score,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/inspections/{inspection_id}/compliance  — Latest result
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=ComplianceResponse,
    summary="Get latest compliance result",
    description=(
        "Return the most recent compliance result for an inspection. "
        "Re-runs the rule logic in-memory against the stored declarations "
        "so the check list always reflects the current ruleset, "
        "while violations are read from the database."
    ),
)
def get_compliance_result(
    inspection_id: int,
    db: DBSession,
) -> ComplianceResponse:
    inspection = _get_inspection_or_404(inspection_id, db)

    # Re-run engine in-memory (read-only, no writes)
    decl_rows = (
        db.query(Declaration)
        .filter(Declaration.inspection_id == inspection_id)
        .all()
    )
    declarations: dict[str, str | None] = {d.field_name: d.value for d in decl_rows}
    result = run_compliance(declarations)

    # Load persisted violations from DB
    stored_violations = (
        db.query(Violation)
        .filter(Violation.inspection_id == inspection_id)
        .order_by(Violation.id.asc())
        .all()
    )

    return _build_response(
        inspection_id=inspection_id,
        inspection=inspection,
        checks=result.checks,
        violations=stored_violations,
        total_checks=result.total_checks,
        passed_checks=result.passed_checks,
        failed_checks=result.failed_checks,
        overall_status=result.overall_status,
        score=result.score,
    )
