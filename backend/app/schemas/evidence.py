"""
Pydantic v2 schemas for the Evidence sub-resource.

Used by:
  POST   /api/v1/inspections/{id}/evidence
  GET    /api/v1/inspections/{id}/evidence
  DELETE /api/v1/evidence/{evidence_id}
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceCreate(BaseModel):
    """Request body for POST /evidence."""

    description: str | None = Field(default=None, description="Text description of the evidence")
    field_name: str | None = Field(default=None, description="Label field this evidence relates to")
    image_id: int | None = Field(default=None, gt=0, description="InspectionImage.id (optional)")
    violation_id: int | None = Field(default=None, gt=0, description="Violation.id (optional)")
    bounding_box: Any | None = Field(
        default=None,
        description='Bounding box JSON, e.g. {"x": 10, "y": 20, "w": 100, "h": 50}',
    )
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Confidence score 0–1"
    )


class EvidenceRead(BaseModel):
    """Response schema for a single Evidence record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    image_id: int | None = None
    violation_id: int | None = None
    description: str | None = None
    field_name: str | None = None
    bounding_box: Any | None = None
    confidence: float | None = None
    created_at: datetime


class EvidenceDeleteResponse(BaseModel):
    """Response body for DELETE /evidence/{id}."""

    message: str
    id: int
