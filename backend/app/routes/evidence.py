"""
APIRouter: Evidence

Endpoints
---------
POST   /api/v1/inspections/{inspection_id}/evidence   Create evidence record
GET    /api/v1/inspections/{inspection_id}/evidence   List evidence
DELETE /api/v1/evidence/{evidence_id}                 Delete evidence record
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.evidence import Evidence
from app.models.inspection import Inspection
from app.schemas.evidence import EvidenceCreate, EvidenceDeleteResponse, EvidenceRead

# Two routers: one nested under inspections, one top-level for delete-by-id
inspection_router = APIRouter(
    prefix="/api/v1/inspections/{inspection_id}/evidence",
    tags=["Evidence"],
)

evidence_router = APIRouter(
    prefix="/api/v1/evidence",
    tags=["Evidence"],
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


def _get_evidence_or_404(evidence_id: int, db: Session) -> Evidence:
    obj = db.get(Evidence, evidence_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with id={evidence_id} not found.",
        )
    return obj


# ---------------------------------------------------------------------------
# POST /api/v1/inspections/{inspection_id}/evidence
# ---------------------------------------------------------------------------

@inspection_router.post(
    "",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create evidence for an inspection",
    description=(
        "Store a piece of evidence associated with an inspection finding. "
        "Optionally link to a specific image (`image_id`) or violation (`violation_id`). "
        "Bounding-box coordinates may be supplied by the AI/OCR layer."
    ),
)
def create_evidence(
    inspection_id: int,
    payload: EvidenceCreate,
    db: DBSession,
) -> Evidence:
    _get_inspection_or_404(inspection_id, db)
    ev = Evidence(
        inspection_id=inspection_id,
        image_id=payload.image_id,
        violation_id=payload.violation_id,
        description=payload.description,
        field_name=payload.field_name,
        bounding_box=payload.bounding_box,
        confidence=payload.confidence,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


# ---------------------------------------------------------------------------
# GET /api/v1/inspections/{inspection_id}/evidence
# ---------------------------------------------------------------------------

@inspection_router.get(
    "",
    response_model=list[EvidenceRead],
    summary="List evidence for an inspection",
    description="Return all evidence records for the specified inspection.",
)
def list_evidence(
    inspection_id: int,
    db: DBSession,
) -> list[Evidence]:
    _get_inspection_or_404(inspection_id, db)
    return (
        db.query(Evidence)
        .filter(Evidence.inspection_id == inspection_id)
        .order_by(Evidence.created_at.asc())
        .all()
    )


# ---------------------------------------------------------------------------
# DELETE /api/v1/evidence/{evidence_id}
# ---------------------------------------------------------------------------

@evidence_router.delete(
    "/{evidence_id}",
    response_model=EvidenceDeleteResponse,
    summary="Delete an evidence record",
    description="Permanently delete an evidence record by its ID.",
)
def delete_evidence(
    evidence_id: int,
    db: DBSession,
) -> EvidenceDeleteResponse:
    ev = _get_evidence_or_404(evidence_id, db)
    db.delete(ev)
    db.commit()
    return EvidenceDeleteResponse(
        message=f"Evidence id={evidence_id} deleted successfully.",
        id=evidence_id,
    )
