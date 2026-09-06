"""
APIRouter: Reports

Endpoints
---------
POST /api/v1/inspections/{id}/report      Generate PDF compliance report
GET  /api/v1/inspections/{id}/reports     List reports for an inspection
GET  /api/v1/reports/{report_id}/download Download a generated PDF
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.declaration import Declaration
from app.models.evidence import Evidence
from app.models.inspection import Inspection
from app.models.report import Report
from app.models.violation import Violation
from app.schemas.report import ReportRead, ReportSummary
from app.services.compliance import run_compliance
from app.services.report import REPORTS_DIR, generate_pdf

inspection_router = APIRouter(
    prefix="/api/v1/inspections/{inspection_id}",
    tags=["Reports"],
)

report_router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"],
)

DBSession = Annotated[Session, Depends(get_db)]


def _get_inspection_or_404(inspection_id: int, db: Session) -> Inspection:
    obj = db.get(Inspection, inspection_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with id={inspection_id} not found.",
        )
    return obj


def _get_report_or_404(report_id: int, db: Session) -> Report:
    obj = db.get(Report, report_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with id={report_id} not found.",
        )
    return obj


# ---------------------------------------------------------------------------
# POST /api/v1/inspections/{inspection_id}/report
# ---------------------------------------------------------------------------

@inspection_router.post(
    "/report",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate compliance inspection report",
    description=(
        "Generate a PDF compliance inspection report for this inspection. "
        "The report includes label declarations, compliance summary, violations, "
        "and evidence. The PDF is saved to `backend/reports/` and a SHA-256 hash "
        "is computed. The report metadata is stored in the `reports` table."
    ),
)
def generate_report(
    inspection_id: int,
    db: DBSession,
) -> ReportRead:
    inspection = _get_inspection_or_404(inspection_id, db)

    # Load declarations
    decl_rows = (
        db.query(Declaration)
        .filter(Declaration.inspection_id == inspection_id)
        .all()
    )
    declarations: dict[str, str | None] = {d.field_name: d.value for d in decl_rows}

    # Run compliance engine (read-only — for the PDF snapshot)
    comp_result = run_compliance(declarations)

    # Load persisted violations
    violation_rows = (
        db.query(Violation)
        .filter(Violation.inspection_id == inspection_id)
        .order_by(Violation.id.asc())
        .all()
    )
    violations_data = [
        {
            "field_name": v.field_name,
            "severity": v.severity,
            "description": v.description,
        }
        for v in violation_rows
    ]

    # Load evidence
    evidence_rows = (
        db.query(Evidence)
        .filter(Evidence.inspection_id == inspection_id)
        .order_by(Evidence.id.asc())
        .all()
    )
    evidence_data = [
        {
            "description": e.description,
            "field_name": e.field_name,
            "confidence": e.confidence,
        }
        for e in evidence_rows
    ]

    # Generate PDF
    pdf_path, sha256 = generate_pdf(
        inspection_id=inspection_id,
        reference_number=inspection.reference_number,
        location=inspection.location,
        inspector_name=None,          # inspector FK not resolved yet
        inspection_date=inspection.created_at,
        declarations=declarations,
        overall_status=comp_result.overall_status,
        compliance_score=inspection.compliance_score,
        total_checks=comp_result.total_checks,
        passed_checks=comp_result.passed_checks,
        failed_checks=comp_result.failed_checks,
        violations=violations_data,
        evidence=evidence_data,
    )

    rel_path = f"reports/{pdf_path.name}"

    # Persist report record
    report = Report(
        inspection_id=inspection_id,
        file_path=rel_path,
        file_hash=sha256,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportRead(
        report_id=report.id,
        inspection_id=inspection_id,
        file_name=pdf_path.name,
        download_url=f"/api/v1/reports/{report.id}/download",
        sha256=sha256,
        generated_at=report.generated_at,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/inspections/{inspection_id}/reports
# ---------------------------------------------------------------------------

@inspection_router.get(
    "/reports",
    response_model=list[ReportSummary],
    summary="List reports for an inspection",
    description="Return all generated reports for the specified inspection.",
)
def list_reports(
    inspection_id: int,
    db: DBSession,
) -> list[Report]:
    _get_inspection_or_404(inspection_id, db)
    return (
        db.query(Report)
        .filter(Report.inspection_id == inspection_id)
        .order_by(Report.generated_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# GET /api/v1/reports/{report_id}/download
# ---------------------------------------------------------------------------

@report_router.get(
    "/{report_id}/download",
    summary="Download a generated PDF report",
    description=(
        "Download the PDF report file. Returns `Content-Type: application/pdf`. "
        "Returns 404 if the report record or its file does not exist."
    ),
)
def download_report(
    report_id: int,
    db: DBSession,
) -> FileResponse:
    report = _get_report_or_404(report_id, db)
    if not report.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report has no associated file.",
        )
    # Resolve absolute path safely
    abs_path = (REPORTS_DIR.parent / report.file_path).resolve()
    # Prevent path traversal: ensure resolved path is under REPORTS_DIR
    try:
        abs_path.relative_to(REPORTS_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report file path.",
        )
    if not abs_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found on disk.",
        )
    return FileResponse(
        path=str(abs_path),
        media_type="application/pdf",
        filename=abs_path.name,
    )
