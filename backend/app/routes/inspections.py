"""
APIRouter: Inspections

Prefix : /api/v1/inspections
Tags   : ["Inspections"]

Endpoints
---------
POST   /                        Create a new inspection
GET    /                        List inspections (paginated)
GET    /{inspection_id}         Get a single inspection with related data
PATCH  /{inspection_id}         Update inspection fields
DELETE /{inspection_id}         Delete an inspection
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inspection import Inspection
from app.models.product import Product
from app.schemas.inspection import (
    DeleteResponse,
    InspectionCreate,
    InspectionDetail,
    InspectionSummary,
    InspectionUpdate,
    PaginatedInspections,
    VALID_STATUSES,
)

router = APIRouter(
    prefix="/api/v1/inspections",
    tags=["Inspections"],
)

# Reusable dependency type alias
DBSession = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_or_404(inspection_id: int, db: Session) -> Inspection:
    """Return the Inspection row or raise HTTP 404."""
    obj = db.get(Inspection, inspection_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with id={inspection_id} not found.",
        )
    return obj


# ---------------------------------------------------------------------------
# POST /api/v1/inspections  — Create
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=InspectionSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new inspection",
    description=(
        "Create a new inspection record. "
        "`reference_number` must be unique across all inspections. "
        "Default status is **pending**."
    ),
)
def create_inspection(
    payload: InspectionCreate,
    db: DBSession,
) -> Inspection:
    # Guard: reference_number must be unique
    existing = (
        db.query(Inspection)
        .filter(Inspection.reference_number == payload.reference_number)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An inspection with reference_number "
                f"{payload.reference_number!r} already exists (id={existing.id})."
            ),
        )

    inspection = Inspection(
        reference_number=payload.reference_number,
        location=payload.location,
        inspector_id=payload.inspector_id,
        product_id=payload.product_id,
        status="pending",
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection


# ---------------------------------------------------------------------------
# GET /api/v1/inspections  — List (paginated)
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[InspectionSummary],
    summary="List inspections",
    description=(
        "Return a paginated list of inspections ordered by most-recent first. "
        "Use `skip` and `limit` for pagination."
    ),
)
def list_inspections(
    db: DBSession,
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="Max records to return")] = 20,
    status_filter: Annotated[
        str | None,
        Query(alias="status", description=f"Filter by status. One of: {sorted(VALID_STATUSES)}"),
    ] = None,
) -> list[Inspection]:
    if status_filter is not None and status_filter not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status filter {status_filter!r}. Must be one of: {sorted(VALID_STATUSES)}",
        )

    q = db.query(Inspection)
    if status_filter:
        q = q.filter(Inspection.status == status_filter)

    return (
        q.order_by(Inspection.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ---------------------------------------------------------------------------
# GET /api/v1/inspections/history  — History (paginated + search)
# ---------------------------------------------------------------------------

@router.get(
    "/history",
    response_model=PaginatedInspections,
    summary="Get inspection history",
    description="Return inspection history with pagination, status filter, and text search.",
)
def get_inspection_history(
    db: DBSession,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
    status_filter: Annotated[
        str | None,
        Query(alias="status", description=f"Filter by status. One of: {sorted(VALID_STATUSES)}"),
    ] = None,
    search: Annotated[str | None, Query(description="Search reference_number, location, or product name")] = None,
) -> PaginatedInspections:
    if status_filter is not None and status_filter not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status filter {status_filter!r}. Must be one of: {sorted(VALID_STATUSES)}",
        )

    q = db.query(Inspection)

    if status_filter:
        q = q.filter(Inspection.status == status_filter)
    
    if search:
        search_term = f"%{search}%"
        q = q.outerjoin(Product).filter(
            or_(
                Inspection.reference_number.ilike(search_term),
                Inspection.location.ilike(search_term),
                Product.name.ilike(search_term)
            )
        )

    total = q.count()
    total_pages = (total + page_size - 1) // page_size

    inspections = (
        q.order_by(Inspection.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedInspections(
        items=inspections,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/inspections/{inspection_id}  — Detail
# ---------------------------------------------------------------------------

@router.get(
    "/{inspection_id}",
    response_model=InspectionDetail,
    summary="Get inspection detail",
    description=(
        "Return a single inspection by ID, including its related "
        "images, declarations, violations, and evidence."
    ),
)
def get_inspection(
    inspection_id: int,
    db: DBSession,
) -> Inspection:
    return _get_or_404(inspection_id, db)


# ---------------------------------------------------------------------------
# PATCH /api/v1/inspections/{inspection_id}  — Update
# ---------------------------------------------------------------------------

@router.patch(
    "/{inspection_id}",
    response_model=InspectionSummary,
    summary="Update an inspection",
    description=(
        "Partially update an inspection. "
        "Only `status`, `compliance_score`, `product_id`, and `location` "
        "may be changed. Fields not included in the body are left unchanged."
    ),
)
def update_inspection(
    inspection_id: int,
    payload: InspectionUpdate,
    db: DBSession,
) -> Inspection:
    inspection = _get_or_404(inspection_id, db)

    # Apply only the fields that were explicitly supplied
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No updatable fields were provided in the request body.",
        )

    for field, value in update_data.items():
        setattr(inspection, field, value)

    db.commit()
    db.refresh(inspection)
    return inspection


# ---------------------------------------------------------------------------
# DELETE /api/v1/inspections/{inspection_id}  — Delete
# ---------------------------------------------------------------------------

@router.delete(
    "/{inspection_id}",
    response_model=DeleteResponse,
    summary="Delete an inspection",
    description=(
        "Permanently delete an inspection and all its related records "
        "(images, declarations, violations, evidence, reports) via CASCADE. "
        "This action cannot be undone."
    ),
)
def delete_inspection(
    inspection_id: int,
    db: DBSession,
) -> DeleteResponse:
    inspection = _get_or_404(inspection_id, db)
    ref = inspection.reference_number
    db.delete(inspection)
    db.commit()
    return DeleteResponse(
        message=f"Inspection {ref!r} (id={inspection_id}) deleted successfully.",
        id=inspection_id,
    )
