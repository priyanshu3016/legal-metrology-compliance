"""
Models package — imports every ORM model so that SQLAlchemy's metadata
registry is fully populated before Base.metadata.create_all() is called
in app.database.init_db().

Import order matters:
  1. Models with no FK dependencies (User, Product, Rule)
  2. Inspection (depends on User + Product)
  3. Leaf models that depend on Inspection (and optionally Rule / InspectionImage)
"""

from app.models.user import User  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.rule import Rule  # noqa: F401
from app.models.inspection import Inspection  # noqa: F401
from app.models.inspection_image import InspectionImage  # noqa: F401
from app.models.declaration import Declaration  # noqa: F401
from app.models.violation import Violation  # noqa: F401
from app.models.evidence import Evidence  # noqa: F401
from app.models.report import Report  # noqa: F401

__all__ = [
    "User",
    "Product",
    "Rule",
    "Inspection",
    "InspectionImage",
    "Declaration",
    "Violation",
    "Evidence",
    "Report",
]
