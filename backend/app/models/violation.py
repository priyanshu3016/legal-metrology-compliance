"""
ORM model: Violation

Records a specific rule violation found during compliance evaluation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection
    from app.models.rule import Rule


class Violation(Base):
    """A compliance rule violation detected during an inspection."""

    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    field_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
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
        back_populates="violations",
    )
    rule: Mapped["Rule | None"] = relationship(
        "Rule",
        back_populates="violations",
    )

    def __repr__(self) -> str:
        return (
            f"<Violation id={self.id} inspection_id={self.inspection_id} "
            f"severity={self.severity!r} status={self.status!r}>"
        )
