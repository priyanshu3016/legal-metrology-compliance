"""
Pydantic v2 schemas for the Report sub-resource.

Used by:
  POST /api/v1/inspections/{id}/report
  GET  /api/v1/inspections/{id}/reports
  GET  /api/v1/reports/{report_id}/download
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportRead(BaseModel):
    """Full response returned after generating a report."""

    model_config = ConfigDict(from_attributes=True)

    report_id: int
    inspection_id: int
    file_name: str
    download_url: str
    sha256: str
    generated_at: datetime


class ReportSummary(BaseModel):
    """Lightweight schema used in the list-reports endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    file_path: str | None = None
    file_hash: str | None = None
    generated_at: datetime
