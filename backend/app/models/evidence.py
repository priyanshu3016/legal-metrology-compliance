"""
ORM model: Evidence

Stores supporting evidence (e.g. bounding-box regions on a label image)
for a violation or general inspection finding.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection
    from app.models.inspection_image import InspectionImage


class Evidence(Base):
    """Supporting evidence linked to an inspection, optionally pinned to an image."""

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("inspection_images.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    field_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    # JSON column stores bounding-box coordinates: {"x": 10, "y": 20, "w": 100, "h": 50}
    bounding_box: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    violation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("violations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    inspection: Mapped["Inspection"] = relationship(
        "Inspection",
        back_populates="evidence",
    )
    image: Mapped["InspectionImage | None"] = relationship(
        "InspectionImage",
    )

    def __repr__(self) -> str:
        return (
            f"<Evidence id={self.id} inspection_id={self.inspection_id} "
            f"image_id={self.image_id}>"
        )
