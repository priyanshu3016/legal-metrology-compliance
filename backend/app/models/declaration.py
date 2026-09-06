"""
ORM model: Declaration

Stores individual field-level data extracted from a product label.
Each row represents one declared field (e.g. "mrp", "net_quantity").

Example field_name values:
  product_name, manufacturer, net_quantity, mrp,
  manufacturing_date, consumer_care, country_of_origin,
  best_before, unit_sale_price
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class Declaration(Base):
    """A single labelling field extracted (manually or via OCR) from a label."""

    __tablename__ = "declarations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_name: Mapped[str] = mapped_column(String(150), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
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
        back_populates="declarations",
    )

    def __repr__(self) -> str:
        return (
            f"<Declaration id={self.id} field={self.field_name!r} "
            f"status={self.status!r}>"
        )
