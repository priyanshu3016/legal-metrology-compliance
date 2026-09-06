"""
ORM model: Report

Stores metadata for a generated compliance inspection report.
The actual PDF/file lives on disk under reports/.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class Report(Base):
    """Generated compliance report metadata for an inspection."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    inspection: Mapped["Inspection"] = relationship(
        "Inspection",
        back_populates="reports",
    )

    def __repr__(self) -> str:
        return (
            f"<Report id={self.id} inspection_id={self.inspection_id} "
            f"generated_at={self.generated_at}>"
        )
