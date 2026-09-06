"""
ORM model: Product

Represents a packaged product that can be inspected.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class Product(Base):
    """A packaged commodity subject to legal metrology compliance checks."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    inspections: Mapped[list["Inspection"]] = relationship(
        "Inspection",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r}>"
