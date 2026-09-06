"""
Pydantic v2 schemas for the AI/OCR extracted-data sub-resource.

Used by:
  POST /api/v1/inspections/{id}/extracted-data
  GET  /api/v1/inspections/{id}/extracted-data

Architecture note:
  AI/OCR extracts facts -> Backend stores them as Declaration rows.
  A separate deterministic rules engine (Step 7) will evaluate compliance.
  This layer does NOT make compliance decisions.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Known label field names (informational only — extras are allowed)
# ---------------------------------------------------------------------------
KNOWN_LABEL_FIELDS: list[str] = [
    "product_name",
    "manufacturer",
    "packer",
    "importer",
    "brand",
    "commodity_category",
    "net_quantity",
    "mrp",
    "date_of_manufacturing",
    "date_of_packing",
    "best_before",
    "use_by",
    "consumer_care",
    "country_of_origin",
    "unit_sale_price",
]


# ---------------------------------------------------------------------------
# Request: POST extracted-data
# ---------------------------------------------------------------------------

class ExtractedDataSubmit(BaseModel):
    """
    Body for POST /api/v1/inspections/{id}/extracted-data.

    Each non-null top-level field becomes (or updates) a Declaration row
    in the database.  The optional 'confidence' mapping carries per-field
    OCR confidence scores (0.0 – 1.0).

    All label fields are optional; send only what the OCR extracted.
    """

    # --- label fields (all optional) ---
    product_name: str | None = Field(default=None, description="Product name as printed on label")
    manufacturer: str | None = Field(default=None, description="Manufacturer name and address")
    packer: str | None = Field(default=None, description="Packer (if different from manufacturer)")
    importer: str | None = Field(default=None, description="Importer details (imported goods)")
    brand: str | None = Field(default=None, description="Brand name")
    commodity_category: str | None = Field(default=None, description="Commodity category under LM Act")
    net_quantity: str | None = Field(default=None, description="Net quantity (e.g. '1 kg', '500 ml')")
    mrp: str | None = Field(default=None, description="Maximum retail price as printed (e.g. 'Rs.30')")
    date_of_manufacturing: str | None = Field(default=None, description="Date of manufacturing (as printed)")
    date_of_packing: str | None = Field(default=None, description="Date of packing (as printed)")
    best_before: str | None = Field(default=None, description="Best before / shelf life")
    use_by: str | None = Field(default=None, description="Use-by / expiry date (as printed)")
    consumer_care: str | None = Field(default=None, description="Consumer care contact details")
    country_of_origin: str | None = Field(default=None, description="Country of origin")
    unit_sale_price: str | None = Field(default=None, description="Unit sale price (if applicable)")

    # --- optional confidence map ---
    confidence: dict[str, float] | None = Field(
        default=None,
        description=(
            "Per-field OCR confidence scores (0.0 = no confidence, 1.0 = certain). "
            "Only include fields for which confidence is known."
        ),
    )

    @model_validator(mode="after")
    def validate_confidence_range(self) -> "ExtractedDataSubmit":
        if self.confidence:
            bad = {k: v for k, v in self.confidence.items() if not (0.0 <= v <= 1.0)}
            if bad:
                raise ValueError(
                    f"Confidence values must be between 0.0 and 1.0. "
                    f"Out-of-range fields: {bad}"
                )
        return self

    def label_fields(self) -> dict[str, str | None]:
        """Return only the label-field key/value pairs (excludes confidence)."""
        return self.model_dump(exclude={"confidence"}, exclude_none=False)


# ---------------------------------------------------------------------------
# Response: single declaration row
# ---------------------------------------------------------------------------

class DeclarationRead(BaseModel):
    """Read schema for one extracted declaration row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    field_name: str
    value: str | None = None
    confidence: float | None = None
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Response: GET extracted-data (frontend-friendly aggregated view)
# ---------------------------------------------------------------------------

class ExtractedDataResponse(BaseModel):
    """
    Aggregated response for GET /api/v1/inspections/{id}/extracted-data.

    Presents declarations as a flat key->value map plus a separate
    key->confidence map, matching the shape AI/OCR teams submitted.
    """

    inspection_id: int
    extraction_status: str = Field(
        description="Overall inspection status reflecting the extraction stage."
    )
    extracted_data: dict[str, str | None] = Field(
        default_factory=dict,
        description="Field name -> extracted text value.",
    )
    confidence: dict[str, float] = Field(
        default_factory=dict,
        description="Field name -> OCR confidence (only fields with a confidence value).",
    )
    declarations: list[DeclarationRead] = Field(
        default_factory=list,
        description="Raw declaration rows for detailed inspection.",
    )
