"""
APIRouter: AI/OCR Extracted Data

Prefix : /api/v1/inspections/{inspection_id}/extracted-data
Tags   : ["Extracted Data"]

Architecture
------------
AI/OCR pipeline extracts facts from label images.
This router receives those facts and stores each one as a Declaration row.
A deterministic rules engine (Step 7) will later read the stored declarations
and decide whether they satisfy Legal Metrology requirements.

This layer does NOT make compliance decisions.

Endpoints
---------
POST /  - Submit (or re-submit) extracted label data for an inspection.
          Performs an upsert: existing fields are updated, new fields are
          created, unmentioned fields are left untouched.
          Sets inspection.status -> "processing" before storing, then
          -> "completed" after a successful commit.

GET  /  - Return the current extracted data for an inspection in a
          frontend-friendly aggregated format.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.declaration import Declaration
from app.models.inspection import Inspection
from app.schemas.extraction import (
    DeclarationRead,
    ExtractedDataResponse,
    ExtractedDataSubmit,
)

router = APIRouter(
    prefix="/api/v1/inspections/{inspection_id}/extracted-data",
    tags=["Extracted Data"],
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


def _upsert_declaration(
    inspection_id: int,
    field_name: str,
    value: str | None,
    confidence: float | None,
    db: Session,
) -> Declaration:
    """
    Update an existing Declaration row for (inspection_id, field_name),
    or create a new one if it does not exist.

    Status is always set to 'extracted' to signal that the value came
    from the AI/OCR pipeline.
    """
    existing = (
        db.query(Declaration)
        .filter(
            Declaration.inspection_id == inspection_id,
            Declaration.field_name == field_name,
        )
        .first()
    )
    if existing:
        existing.value = value
        existing.confidence = confidence
        existing.status = "extracted"
        return existing
    else:
        decl = Declaration(
            inspection_id=inspection_id,
            field_name=field_name,
            value=value,
            confidence=confidence,
            status="extracted",
        )
        db.add(decl)
        return decl


# ---------------------------------------------------------------------------
# POST /api/v1/inspections/{inspection_id}/extracted-data
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ExtractedDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit AI/OCR extracted label data",
    description=(
        "Receive structured label data extracted by the AI/OCR pipeline and "
        "persist each field as an individual Declaration row. "
        "Re-submitting performs an **upsert**: existing fields are updated, "
        "new fields are inserted, unmentioned fields are left unchanged. "
        "Sets `inspection.status` to **processing** at the start and "
        "**completed** after a successful commit. "
        "Does **not** evaluate legal compliance — that is done by the rules engine."
    ),
)
def submit_extracted_data(
    inspection_id: int,
    payload: ExtractedDataSubmit,
    db: DBSession,
) -> ExtractedDataResponse:
    inspection = _get_inspection_or_404(inspection_id, db)

    # --- collect all submitted label fields (skip None values) ---
    label_fields = payload.label_fields()
    submitted_fields = {k: v for k, v in label_fields.items() if v is not None}

    if not submitted_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No label field values were provided. Submit at least one non-null field.",
        )

    confidence_map: dict[str, float] = payload.confidence or {}

    # --- mark inspection as processing ---
    inspection.status = "processing"
    db.flush()

    # --- upsert each field ---
    for field_name, value in submitted_fields.items():
        conf = confidence_map.get(field_name)
        _upsert_declaration(inspection_id, field_name, value, conf, db)

    # --- mark inspection as completed ---
    inspection.status = "completed"
    db.commit()
    db.refresh(inspection)

    # --- re-query all declarations for this inspection ---
    all_decls = (
        db.query(Declaration)
        .filter(Declaration.inspection_id == inspection_id)
        .order_by(Declaration.field_name)
        .all()
    )

    extracted_data = {d.field_name: d.value for d in all_decls}
    conf_out = {d.field_name: d.confidence for d in all_decls if d.confidence is not None}

    return ExtractedDataResponse(
        inspection_id=inspection_id,
        extraction_status=inspection.status,
        extracted_data=extracted_data,
        confidence=conf_out,
        declarations=[DeclarationRead.model_validate(d) for d in all_decls],
    )


# ---------------------------------------------------------------------------
# GET /api/v1/inspections/{inspection_id}/extracted-data
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=ExtractedDataResponse,
    summary="Get extracted label data for an inspection",
    description=(
        "Return all Declaration rows for the given inspection in a "
        "frontend-friendly flat format. "
        "Returns an empty `extracted_data` map if no data has been extracted yet "
        "(does not raise a 404)."
    ),
)
def get_extracted_data(
    inspection_id: int,
    db: DBSession,
) -> ExtractedDataResponse:
    inspection = _get_inspection_or_404(inspection_id, db)

    all_decls = (
        db.query(Declaration)
        .filter(Declaration.inspection_id == inspection_id)
        .order_by(Declaration.field_name)
        .all()
    )

    extracted_data = {d.field_name: d.value for d in all_decls}
    conf_out = {d.field_name: d.confidence for d in all_decls if d.confidence is not None}

    return ExtractedDataResponse(
        inspection_id=inspection_id,
        extraction_status=inspection.status,
        extracted_data=extracted_data,
        confidence=conf_out,
        declarations=[DeclarationRead.model_validate(d) for d in all_decls],
    )
