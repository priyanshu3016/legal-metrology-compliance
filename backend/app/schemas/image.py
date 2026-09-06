"""
Pydantic v2 schemas for the Inspection Image sub-resource.

Used by:
  POST   /api/v1/inspections/{id}/images
  GET    /api/v1/inspections/{id}/images
  DELETE /api/v1/inspections/{id}/images/{image_id}
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImageRead(BaseModel):
    """Response schema for a single uploaded inspection image."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    file_path: str
    panel_type: str | None = None
    uploaded_at: datetime


class ImageUploadResponse(BaseModel):
    """Response schema returned after a successful image upload."""

    model_config = ConfigDict(from_attributes=True)

    uploaded: int
    images: list[ImageRead]


class ImageDeleteResponse(BaseModel):
    """Response body for a DELETE image request."""

    message: str
    id: int
