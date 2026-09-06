"""
ORM model: Inspection

Central record linking a product, an inspector, uploaded images,
extracted declarations, violations, evidence, and generated reports.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product
    from app.models.inspection_image import InspectionImage
    from app.models.declaration import Declaration
    from app.models.violation import Violation
    from app.models.evidence import Evidence
    from app.models.report import Report


class Inspection(Base):
    """An inspection session for a single product label."""

    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    inspector_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reference_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    inspector: Mapped["User | None"] = relationship(
        "User",
        back_populates="inspections",
    )
    product: Mapped["Product | None"] = relationship(
        "Product",
        back_populates="inspections",
    )
    images: Mapped[list["InspectionImage"]] = relationship(
        "InspectionImage",
        back_populates="inspection",
        cascade="all, delete-orphan",
    )
    declarations: Mapped[list["Declaration"]] = relationship(
        "Declaration",
        back_populates="inspection",
        cascade="all, delete-orphan",
    )
    violations: Mapped[list["Violation"]] = relationship(
        "Violation",
        back_populates="inspection",
        cascade="all, delete-orphan",
    )
    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence",
        back_populates="inspection",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="inspection",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Inspection id={self.id} ref={self.reference_number!r} "
            f"status={self.status!r}>"
        )
