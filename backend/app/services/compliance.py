"""
Compliance Rules Engine — app/services/compliance.py

Deterministic, pure-Python compliance checks for Legal Metrology Act declarations.

Architecture
------------
  AI/OCR  ->  Declaration rows  ->  [THIS SERVICE]  ->  Violation rows
                                          |
                               Returns ComplianceResult
                               (no AI / no LLM involved)

Each RuleSpec defines:
  - field_name   : the Declaration.field_name it targets
  - rule_code    : short identifier (used as Violation.description prefix)
  - description  : human-readable rule description
  - severity     : LOW | MEDIUM | HIGH
  - check_fn     : callable(value: str | None) -> (passed: bool, message: str)

The engine:
  1. Iterates over all RuleSpecs.
  2. Looks up the corresponding Declaration row.
  3. Calls check_fn with the stored value.
  4. Collects CheckResult objects.
  5. Calculates score = passed / total * 100.
  6. Returns a ComplianceResult dataclass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Result dataclasses (pure Python, no SQLAlchemy / Pydantic dependency)
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Result of a single rule check."""
    field_name: str
    rule_code: str
    status: str          # "PASS" | "FAIL"
    message: str
    severity: str        # "LOW" | "MEDIUM" | "HIGH"


@dataclass
class ComplianceResult:
    """Aggregate result returned by run_compliance()."""
    overall_status: str            # "COMPLIANT" | "NON_COMPLIANT"
    score: float                   # 0.0 – 100.0, rounded to 2 dp
    total_checks: int
    passed_checks: int
    failed_checks: int
    checks: list[CheckResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

_NUMERIC_RE = re.compile(r"\d+(?:[.,]\d+)?")

# Supported quantity units — LM Act schedule reference
_QUANTITY_UNITS = re.compile(
    r"\b(mg|g|kg|ml|l|litre|liter|liters|litres|cl|dl|cm|m|mm|"
    r"units?|pcs?|pieces?|nos?|tablets?|capsules?|sachets?|packs?|pairs?)\b",
    re.IGNORECASE,
)

# Minimal consumer care pattern: phone number OR email OR "address" keyword
# Phone: at least 6 digits (after stripping non-digit chars, e.g. 1800-123-4567 -> 11 digits)
_PHONE_DIGITS_RE = re.compile(r"\d[\d\s().+-]{4,}\d")  # digit run with separators
_PHONE_CLEAN_RE  = re.compile(r"[^\d]")                 # for stripping non-digits
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.\w+")
_ADDRESS_KEYWORDS = re.compile(
    r"\b(road|street|nagar|colony|district|city|state|pin|toll|free|helpline|care)\b",
    re.IGNORECASE,
)


def _is_present(value: str | None) -> tuple[bool, str]:
    """Pass if value is non-null and non-empty after stripping whitespace."""
    if value and value.strip():
        return True, f"Value present: {value.strip()[:80]}"
    return False, "Declaration is missing or empty"


def _check_net_quantity(value: str | None) -> tuple[bool, str]:
    if not value or not value.strip():
        return False, "Net quantity is missing or empty"
    v = value.strip()
    has_number = bool(_NUMERIC_RE.search(v))
    has_unit = bool(_QUANTITY_UNITS.search(v))
    if has_number and has_unit:
        return True, f"Net quantity valid: {v}"
    if not has_number:
        return False, f"Net quantity has no numeric value: {v!r}"
    return False, f"Net quantity has no recognizable unit: {v!r}"


def _check_mrp(value: str | None) -> tuple[bool, str]:
    if not value or not value.strip():
        return False, "MRP is missing or empty"
    v = value.strip()
    # Accept values like "Rs.30", "INR 30", "30.00", "₹ 30", "MRP Rs 30"
    if _NUMERIC_RE.search(v):
        return True, f"MRP contains numeric price: {v}"
    return False, f"MRP has no recognizable numeric price: {v!r}"


def _check_unit_sale_price(value: str | None) -> tuple[bool, str]:
    """Unit sale price is optional but must be numeric if present."""
    if not value or not value.strip():
        # Absence is acceptable (not all products need it)
        return True, "Unit sale price not declared (optional field)"
    v = value.strip()
    if _NUMERIC_RE.search(v):
        return True, f"Unit sale price valid: {v}"
    return False, f"Unit sale price has no numeric value: {v!r}"


def _check_consumer_care(value: str | None) -> tuple[bool, str]:
    if not value or not value.strip():
        return False, "Consumer care details are missing or empty"
    v = value.strip()
    # Check for email
    has_email = bool(_EMAIL_RE.search(v))
    # Check for phone: a sequence that looks like a phone number
    # (digits possibly separated by hyphens, spaces, parentheses, dots)
    # Strip separators and check total digit count >= 6
    phone_match = _PHONE_DIGITS_RE.search(v)
    has_phone = False
    if phone_match:
        digits_only = _PHONE_CLEAN_RE.sub("", phone_match.group())
        has_phone = len(digits_only) >= 6
    # Check for address keywords
    has_addr = bool(_ADDRESS_KEYWORDS.search(v))
    if has_phone or has_email or has_addr:
        return True, f"Consumer care details present: {v[:80]}"
    return False, (
        f"Consumer care details appear incomplete "
        f"(no phone/email/address detected): {v!r}"
    )


def _check_date_field(value: str | None) -> tuple[bool, str]:
    """Manufacturing/packing date: must be non-empty."""
    return _is_present(value)


def _check_best_before(value: str | None) -> tuple[bool, str]:
    """Best-before / use-by: must be non-empty."""
    return _is_present(value)


# ---------------------------------------------------------------------------
# Rule specification catalogue
# ---------------------------------------------------------------------------

@dataclass
class RuleSpec:
    field_name: str
    rule_code: str
    description: str
    severity: str   # LOW | MEDIUM | HIGH
    check_fn: object   # callable(str | None) -> (bool, str)


# Rules ordered by Legal Metrology Act priority
RULES: list[RuleSpec] = [
    RuleSpec(
        field_name="product_name",
        rule_code="LM-R001",
        description="Product name must be declared on the label",
        severity="HIGH",
        check_fn=_is_present,
    ),
    RuleSpec(
        field_name="manufacturer",
        rule_code="LM-R002",
        description="Manufacturer / Packer / Importer must be declared",
        severity="HIGH",
        check_fn=_is_present,
    ),
    RuleSpec(
        field_name="net_quantity",
        rule_code="LM-R003",
        description="Net quantity must include a numeric value and a valid unit",
        severity="HIGH",
        check_fn=_check_net_quantity,
    ),
    RuleSpec(
        field_name="mrp",
        rule_code="LM-R004",
        description="MRP (Maximum Retail Price) must contain a numeric price",
        severity="HIGH",
        check_fn=_check_mrp,
    ),
    RuleSpec(
        field_name="date_of_manufacturing",
        rule_code="LM-R005",
        description="Date of manufacturing / packing must be declared",
        severity="MEDIUM",
        check_fn=_check_date_field,
    ),
    RuleSpec(
        field_name="date_of_packing",
        rule_code="LM-R005B",
        description="Date of packing must be declared (if manufacturing date absent)",
        severity="MEDIUM",
        check_fn=_check_date_field,
    ),
    RuleSpec(
        field_name="best_before",
        rule_code="LM-R006",
        description="Best-before / use-by / expiry must be declared for perishables",
        severity="MEDIUM",
        check_fn=_check_best_before,
    ),
    RuleSpec(
        field_name="consumer_care",
        rule_code="LM-R007",
        description="Consumer care contact (phone/email/address) must be present",
        severity="MEDIUM",
        check_fn=_check_consumer_care,
    ),
    RuleSpec(
        field_name="country_of_origin",
        rule_code="LM-R008",
        description="Country of origin must be declared",
        severity="LOW",
        check_fn=_is_present,
    ),
    RuleSpec(
        field_name="unit_sale_price",
        rule_code="LM-R009",
        description="Unit sale price must be numeric when declared",
        severity="LOW",
        check_fn=_check_unit_sale_price,
    ),
]


# ---------------------------------------------------------------------------
# Main engine function
# ---------------------------------------------------------------------------

def run_compliance(declarations: dict[str, str | None]) -> ComplianceResult:
    """
    Run all deterministic compliance rules against a dict of declarations.

    Parameters
    ----------
    declarations : dict mapping field_name -> value (str or None)
        Typically built from Declaration ORM rows for one inspection.

    Returns
    -------
    ComplianceResult
        Contains per-check results, overall status, and numeric score.

    No database writes are performed here — this is a pure computation.
    The caller (route handler) is responsible for persisting violations.
    """
    checks: list[CheckResult] = []

    for rule in RULES:
        value = declarations.get(rule.field_name)          # None if not declared
        passed, message = rule.check_fn(value)             # type: ignore[call-arg]
        checks.append(CheckResult(
            field_name=rule.field_name,
            rule_code=rule.rule_code,
            status="PASS" if passed else "FAIL",
            message=message,
            severity=rule.severity,
        ))

    total = len(checks)
    passed_count = sum(1 for c in checks if c.status == "PASS")
    failed_count = total - passed_count

    score = round(passed_count / total * 100, 2) if total else 0.0
    overall = "COMPLIANT" if failed_count == 0 else "NON_COMPLIANT"

    return ComplianceResult(
        overall_status=overall,
        score=score,
        total_checks=total,
        passed_checks=passed_count,
        failed_checks=failed_count,
        checks=checks,
    )
