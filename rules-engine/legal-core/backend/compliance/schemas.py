"""
Compliance Pydantic Schemas for Legal Metrology (Packaged Commodities) Rules, 2011.

Defines:
- Input contract (§4.1): Structured OCR/LLM facts consumed by deterministic check validators.
- Output contract (§4.2): Check results, evidence, citations, and summary metrics.
"""

from typing import Optional, Any, List
from pydantic import BaseModel, Field


# ==============================================================================
# Input Models (§4.1 — what OCR/LLM extraction produces)
# ==============================================================================

class BoundingBox(BaseModel):
    """Bounding box coordinates on the packaging image."""
    x: int
    y: int
    width: int
    height: int


class ExtractedField(BaseModel):
    """Generic wrapper for an extracted label entity with confidence and coordinates."""
    value: Any
    confidence: Optional[float] = None
    raw_text: Optional[str] = None
    bounding_box: Optional[BoundingBox] = None


class NetQuantityValue(BaseModel):
    """Structured net quantity values."""
    numeric: float
    unit: str


class MRPValue(BaseModel):
    """Structured Maximum Retail Price values."""
    amount: float
    currency: str = "INR"
    includes_tax: bool = True
    tax_declaration_text: Optional[str] = None


class ManufacturerValue(BaseModel):
    """Structured manufacturer / packer / importer identity."""
    name: str
    address: str
    role: str = "manufacturer"  # "manufacturer" | "packer" | "importer"


class DateValue(BaseModel):
    """Structured month/year of manufacture or packing."""
    month: int
    year: int
    format: Optional[str] = None


class ConsumerCareValue(BaseModel):
    """Structured consumer grievance contact channels."""
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class FactFields(BaseModel):
    """Container for all extracted package declaration fields."""
    product_name: Optional[ExtractedField] = None
    net_quantity: Optional[ExtractedField] = None       # value: NetQuantityValue or dict
    mrp: Optional[ExtractedField] = None                # value: MRPValue or dict
    manufacturer: Optional[ExtractedField] = None       # value: ManufacturerValue or dict
    packer: Optional[ExtractedField] = None             # value: ManufacturerValue or dict
    importer: Optional[ExtractedField] = None           # value: ManufacturerValue or dict
    manufacturing_date: Optional[ExtractedField] = None # value: DateValue or dict
    consumer_care: Optional[ExtractedField] = None      # value: ConsumerCareValue or dict
    country_of_origin: Optional[ExtractedField] = None  # value: str or dict


class StructuredFacts(BaseModel):
    """Canonical OCR structured facts input schema (§4.1)."""
    inspection_id: str
    overall_confidence: float
    image_quality: str = "good"  # "good" | "fair" | "poor"
    raw_text: str = ""
    fields: FactFields
    quantity_qualifiers_detected: List[str] = Field(default_factory=list)
    is_imported_hint: bool = False


# ==============================================================================
# Output Models (§4.2 — what the compliance engine produces)
# ==============================================================================

class LegalSource(BaseModel):
    """Verbatim legal citation attached to a check result."""
    citation: str
    page: int
    text: str
    document: Optional[str] = None
    rule: Optional[str] = None
    sub_rule: Optional[str] = None
    clause: Optional[str] = None


class Evidence(BaseModel):
    """Visual or textual evidence linked to an inspection check."""
    raw_text: Optional[str] = None
    bounding_box: Optional[BoundingBox] = None


class CheckResult(BaseModel):
    """Individual deterministic compliance evaluation result."""
    check_id: str
    rule_name: str
    status: str  # "PASS" | "FAIL" | "REVIEW" | "N/A"
    severity: str  # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    detected_value: Optional[str] = None
    expected: str
    confidence: Optional[float] = None
    reason: str
    evidence: Optional[Evidence] = None
    legal_source: Optional[LegalSource] = None


class ComplianceSummary(BaseModel):
    """Statistical summary of inspection checks."""
    total_checks: int
    passed: int
    failed: int
    review: int
    not_applicable: int = 0


class ComplianceResult(BaseModel):
    """
    Top-level output schema for the compliance engine evaluation (§4.2).
    Note: automated_check_score is a prototype summary metric and NOT an official legal metric.
    """
    inspection_id: str
    timestamp: str
    overall_status: str  # "PASS" | "FAIL" | "REVIEW"
    automated_check_score: float
    summary: ComplianceSummary
    checks: List[CheckResult]
    disclaimers: List[str] = Field(default_factory=list)

    @property
    def compliance_score(self) -> float:
        """Alias for backward compatibility with prototype UI."""
        return self.automated_check_score
