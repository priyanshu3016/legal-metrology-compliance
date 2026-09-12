"""
Pydantic v2 schemas for the Inspection API.

Separate schemas are used for:
- InspectionCreate   → POST body
- InspectionUpdate   → PATCH body (all fields optional)
- InspectionSummary  → list / dashboard response (lightweight)
- InspectionDetail   → single-record response with nested relations
- Nested read schemas for Declaration, Violation, Evidence, InspectionImage
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Controlled vocabularies
# ---------------------------------------------------------------------------

VALID_STATUSES = {
    "pending",
    "processing",
    "completed",
    "compliant",
    "non_compliant",
    "failed",
}


# ---------------------------------------------------------------------------
# Nested read schemas (child records)
# ---------------------------------------------------------------------------


class DeclarationRead(BaseModel):
    """Lightweight read schema for a label field declaration."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    field_name: str
    value: str | None = None
    status: str
    confidence: float | None = None
    created_at: datetime


class ViolationRead(BaseModel):
    """Read schema for a compliance rule violation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    rule_id: int | None = None
    field_name: str | None = None
    severity: str
    description: str
    confidence: float | None = None
    status: str
    created_at: datetime


class EvidenceRead(BaseModel):
    """Read schema for inspection evidence."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    image_id: int | None = None
    description: str | None = None
    bounding_box: Any | None = None
    confidence: float | None = None
    created_at: datetime


class InspectionImageRead(BaseModel):
    """Read schema for an uploaded label image."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    file_path: str
    panel_type: str | None = None
    uploaded_at: datetime


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class InspectionCreate(BaseModel):
    """Body for POST /api/v1/inspections."""

    reference_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique reference number, e.g. LM-2026-0001",
        examples=["LM-2026-0001"],
    )
    location: str | None = Field(
        default=None,
        max_length=255,
        description="Physical location of the inspection",
        examples=["Delhi"],
    )
    inspector_id: int | None = Field(
        default=None,
        gt=0,
        description="ID of the inspector (users.id)",
    )
    product_id: int | None = Field(
        default=None,
        gt=0,
        description="ID of the inspected product (products.id)",
    )


class InspectionUpdate(BaseModel):
    """Body for PATCH /api/v1/inspections/{id} — all fields optional."""

    status: str | None = Field(
        default=None,
        description=f"One of: {sorted(VALID_STATUSES)}",
    )
    compliance_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Compliance score 0-100",
    )
    product_id: int | None = Field(
        default=None,
        gt=0,
        description="Reassign to a different product",
    )
    location: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status {v!r}. Must be one of: {sorted(VALID_STATUSES)}"
            )
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class InspectionSummary(BaseModel):
    """Lightweight response used in list/dashboard views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_number: str
    location: str | None = None
    inspector_id: int | None = None
    product_id: int | None = None
    product_name: str | None = None
    manufacturer: str | None = None
    status: str
    compliance_score: float | None = None
    created_at: datetime
    updated_at: datetime


class InspectionDetail(BaseModel):
    """Full response for a single inspection including related records."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_number: str
    location: str | None = None
    inspector_id: int | None = None
    product_id: int | None = None
    status: str
    compliance_score: float | None = None
    created_at: datetime
    updated_at: datetime

    # nested relations
    images: list[InspectionImageRead] = []
    declarations: list[DeclarationRead] = []
    violations: list[ViolationRead] = []
    evidence: list[EvidenceRead] = []


class DeleteResponse(BaseModel):
    """Response body for DELETE requests."""

    message: str
    id: int


class PaginatedInspections(BaseModel):
    """Paginated list of inspections."""

    items: list[InspectionSummary]
    total: int
    page: int
    page_size: int
    total_pages: int

