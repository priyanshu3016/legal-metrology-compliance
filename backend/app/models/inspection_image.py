"""
ORM model: InspectionImage

Stores metadata for each label image uploaded during an inspection.
The actual file lives on disk under uploads/.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class InspectionImage(Base):
    """A single label image file associated with an inspection."""

    __tablename__ = "inspection_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    panel_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    inspection: Mapped["Inspection"] = relationship(
        "Inspection",
        back_populates="images",
    )

    def __repr__(self) -> str:
        return (
            f"<InspectionImage id={self.id} inspection_id={self.inspection_id} "
            f"panel={self.panel_type!r}>"
        )
