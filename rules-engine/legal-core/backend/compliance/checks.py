"""
Deterministic Compliance Check Functions for Legal Metrology Rules, 2011.

Pure Python functions evaluating StructuredFacts against regulatory constraints.
Core MVP checks implemented:
- CHK-01: Product/Commodity Name Declaration (Rule 6(1)(b))
- CHK-02: Net Quantity Declaration & SI Units (Rule 6(1)(c), Rule 13)
- CHK-03: Maximum Retail Price (MRP) & Tax Declaration (Rule 6(1)(e), Rule 2(m))
- CHK-04: Manufacturer / Packer / Importer Name & Address (Rule 6(1)(a), Rule 10)
- CHK-05: Month & Year of Manufacture / Pre-packing (Rule 6(1)(d))
- CHK-06: Consumer Care / Grievance Redressal Details (Rule 6(2))

Future Stretch Checks (explicitly reserved for post-MVP):
- CHK-07: Misleading Quantity Qualifiers (Rule 12(6))
- CHK-09: Country of Origin for Imported Goods (Rule 6(1)(a) proviso, Rule 10)
"""

import re
from typing import Optional, Dict, Any, Tuple

from backend.compliance.schemas import (
    StructuredFacts,
    CheckResult,
    LegalSource,
    Evidence,
    ExtractedField,
    BoundingBox
)

CONFIDENCE_FIELD_THRESHOLD = 0.70
CONFIDENCE_IMAGE_FAIL_THRESHOLD = 0.80

VALID_SI_UNITS = {
    "g", "gm", "gram", "grams",
    "kg", "kilogram", "kilograms",
    "ml", "milli-litre", "millilitre", "millilitres",
    "l", "ltr", "litre", "litres", "liter", "liters",
    "m", "meter", "meters", "metre", "metres",
    "cm", "centimeter", "centimeters", "centimetre", "centimetres",
    "mm", "millimeter", "millimeters", "millimetre", "millimetres",
    "n", "u", "pcs", "pieces", "units"
}

NON_SI_UNITS = {
    "oz", "ounce", "ounces",
    "lb", "lbs", "pound", "pounds",
    "fl.oz", "fl oz", "fluid ounce", "fluid ounces"
}

PROHIBITED_QUANTITY_QUALIFIERS = [
    "minimum", "not less than", "approx", "approximately", "average", "when packed"
]


def _extract_field_helper(field: Optional[ExtractedField]) -> Tuple[Any, Optional[float], Optional[str], Optional[BoundingBox]]:
    """Helper to safely extract value, confidence, raw_text, and bounding_box."""
    if field is None:
        return None, None, None, None
    return field.value, field.confidence, field.raw_text, field.bounding_box


# ==============================================================================
# CHK-01: Product Name Declaration (Rule 6(1)(b))
# ==============================================================================
def check_product_name(
    facts: StructuredFacts,
    legal_source: Optional[LegalSource] = None
) -> CheckResult:
    """
    Validates common or generic commodity name declaration under Rule 6(1)(b).
    """
    field = facts.fields.product_name
    val, conf, raw_text, bbox = _extract_field_helper(field)
    evidence = Evidence(raw_text=raw_text, bounding_box=bbox) if field else None

    # Missing check
    if val is None or not str(val).strip():
        if facts.overall_confidence >= CONFIDENCE_IMAGE_FAIL_THRESHOLD:
            return CheckResult(
                check_id="CHK-01",
                rule_name="Product Name Declaration",
                status="FAIL",
                severity="CRITICAL",
                detected_value=None,
                expected="Non-empty generic or common commodity name",
                confidence=facts.overall_confidence,
                reason="Product/commodity name declaration is missing on packaging.",
                evidence=evidence,
                legal_source=legal_source
            )
        else:
            return CheckResult(
                check_id="CHK-01",
                rule_name="Product Name Declaration",
                status="REVIEW",
                severity="CRITICAL",
                detected_value=None,
                expected="Non-empty generic or common commodity name",
                confidence=facts.overall_confidence,
                reason="Product name not detected, but overall image confidence is below 0.80; manual review required.",
                evidence=evidence,
                legal_source=legal_source
            )

    effective_conf = conf if conf is not None else facts.overall_confidence
    str_val = str(val).strip()

    if effective_conf < CONFIDENCE_FIELD_THRESHOLD:
        return CheckResult(
            check_id="CHK-01",
            rule_name="Product Name Declaration",
            status="REVIEW",
            severity="CRITICAL",
            detected_value=str_val,
            expected="Non-empty generic or common commodity name",
            confidence=effective_conf,
            reason=f"Product name detected ('{str_val}'), but confidence ({effective_conf:.2f}) is below 0.70 threshold.",
            evidence=evidence,
            legal_source=legal_source
        )

    if not re.search(r'[a-zA-Z]', str_val):
        return CheckResult(
            check_id="CHK-01",
            rule_name="Product Name Declaration",
            status="FAIL",
            severity="CRITICAL",
            detected_value=str_val,
            expected="Non-empty generic or common commodity name containing alphabetic text",
            confidence=effective_conf,
            reason=f"Detected product name ('{str_val}') does not contain valid alphabetic commodity name.",
            evidence=evidence,
            legal_source=legal_source
        )

    return CheckResult(
        check_id="CHK-01",
        rule_name="Product Name Declaration",
        status="PASS",
        severity="CRITICAL",
        detected_value=str_val,
        expected="Non-empty generic or common commodity name",
        confidence=effective_conf,
        reason="Common or generic commodity name declared with sufficient confidence.",
        evidence=evidence,
        legal_source=legal_source
    )


# ==============================================================================
# CHK-02: Net Quantity Declaration & Units (Rule 6(1)(c), Rule 13)
# ==============================================================================
def check_net_quantity(
    facts: StructuredFacts,
    legal_source: Optional[LegalSource] = None
) -> CheckResult:
    """
    Validates net quantity declaration in standard SI units under Rule 6(1)(c) and Rule 13.
    """
    field = facts.fields.net_quantity
    val, conf, raw_text, bbox = _extract_field_helper(field)
    evidence = Evidence(raw_text=raw_text, bounding_box=bbox) if field else None

    # Missing check
    if val is None:
        if facts.overall_confidence >= CONFIDENCE_IMAGE_FAIL_THRESHOLD:
            return CheckResult(
                check_id="CHK-02",
                rule_name="Net Quantity Declaration",
                status="FAIL",
                severity="CRITICAL",
                detected_value=None,
                expected="Net quantity in standard SI units (g, kg, ml, l, n)",
                confidence=facts.overall_confidence,
                reason="Net quantity declaration is missing on packaging.",
                evidence=evidence,
                legal_source=legal_source
            )
        else:
            return CheckResult(
                check_id="CHK-02",
                rule_name="Net Quantity Declaration",
                status="REVIEW",
                severity="CRITICAL",
                detected_value=None,
                expected="Net quantity in standard SI units (g, kg, ml, l, n)",
                confidence=facts.overall_confidence,
                reason="Net quantity not detected, but overall image confidence is below 0.80; manual review required.",
                evidence=evidence,
                legal_source=legal_source
            )

    effective_conf = conf if conf is not None else facts.overall_confidence

    if effective_conf < CONFIDENCE_FIELD_THRESHOLD:
        return CheckResult(
            check_id="CHK-02",
            rule_name="Net Quantity Declaration",
            status="REVIEW",
            severity="CRITICAL",
            detected_value=raw_text or str(val),
            expected="Net quantity in standard SI units (g, kg, ml, l, n)",
            confidence=effective_conf,
            reason=f"Net quantity detected, but confidence ({effective_conf:.2f}) is below 0.70 threshold.",
            evidence=evidence,
            legal_source=legal_source
        )

    # Extract numeric and unit
    numeric: Optional[float] = None
    unit: Optional[str] = None

    if isinstance(val, dict):
        numeric = val.get("numeric")
        unit = val.get("unit")
    else:
        numeric = getattr(val, "numeric", None)
        unit = getattr(val, "unit", None)

    detected_display = raw_text or f"{numeric} {unit}"

    if numeric is None or float(numeric) <= 0:
        return CheckResult(
            check_id="CHK-02",
            rule_name="Net Quantity Declaration",
            status="FAIL",
            severity="CRITICAL",
            detected_value=detected_display,
            expected="Positive numeric net quantity",
            confidence=effective_conf,
            reason=f"Net quantity numeric value ({numeric}) must be greater than zero.",
            evidence=evidence,
            legal_source=legal_source
        )

    norm_unit = str(unit).strip().lower() if unit else ""

    if norm_unit in NON_SI_UNITS:
        return CheckResult(
            check_id="CHK-02",
            rule_name="Net Quantity Declaration",
            status="FAIL",
            severity="CRITICAL",
            detected_value=detected_display,
            expected="SI standard units of weight or measure",
            confidence=effective_conf,
            reason=f"Unit '{unit}' is a non-standard unit prohibited under Rule 13(5). Standard SI units required.",
            evidence=evidence,
            legal_source=legal_source
        )

    if norm_unit not in VALID_SI_UNITS:
        return CheckResult(
            check_id="CHK-02",
            rule_name="Net Quantity Declaration",
            status="REVIEW",
            severity="CRITICAL",
            detected_value=detected_display,
            expected="Recognized SI standard units (g, kg, ml, l, m, cm, mm, n, u)",
            confidence=effective_conf,
            reason=f"Unit '{unit}' could not be definitively validated as a standard SI unit.",
            evidence=evidence,
            legal_source=legal_source
        )

    # Check for prohibited qualifiers near quantity
    found_qualifiers = [
        q for q in (facts.quantity_qualifiers_detected or [])
        if any(pq in q.lower() for pq in PROHIBITED_QUANTITY_QUALIFIERS)
    ]
    if not found_qualifiers and raw_text:
        found_qualifiers = [
            pq for pq in PROHIBITED_QUANTITY_QUALIFIERS
            if pq in raw_text.lower()
        ]

    if found_qualifiers:
        return CheckResult(
            check_id="CHK-02",
            rule_name="Net Quantity Declaration",
            status="FAIL",
            severity="CRITICAL",
            detected_value=detected_display,
            expected="Net quantity without misleading qualifiers",
            confidence=effective_conf,
            reason=f"Net quantity contains prohibited qualifier(s): {', '.join(found_qualifiers)}.",
            evidence=evidence,
            legal_source=legal_source
        )

    return CheckResult(
        check_id="CHK-02",
        rule_name="Net Quantity Declaration",
        status="PASS",
        severity="CRITICAL",
        detected_value=detected_display,
        expected="Net quantity in standard SI units (g, kg, ml, l, n)",
        confidence=effective_conf,
        reason=f"Net quantity declared in standard SI units ({detected_display}).",
        evidence=evidence,
        legal_source=legal_source
    )


# ==============================================================================
# CHK-03: Maximum Retail Price (MRP) Declaration (Rule 6(1)(e), Rule 2(m))
# ==============================================================================
def check_mrp(
    facts: StructuredFacts,
    legal_source: Optional[LegalSource] = None
) -> CheckResult:
    """
    Validates Maximum Retail Price (MRP) declaration including tax inclusion under Rule 6(1)(e) and Rule 2(m).
    """
    field = facts.fields.mrp
    val, conf, raw_text, bbox = _extract_field_helper(field)
    evidence = Evidence(raw_text=raw_text, bounding_box=bbox) if field else None

    # Missing check
    if val is None:
        if facts.overall_confidence >= CONFIDENCE_IMAGE_FAIL_THRESHOLD:
            return CheckResult(
                check_id="CHK-03",
                rule_name="MRP Declaration",
                status="FAIL",
                severity="CRITICAL",
                detected_value=None,
                expected="Maximum Retail Price (MRP) in INR inclusive of all taxes",
                confidence=facts.overall_confidence,
                reason="Maximum Retail Price (MRP) declaration is missing on packaging.",
                evidence=evidence,
                legal_source=legal_source
            )
        else:
            return CheckResult(
                check_id="CHK-03",
                rule_name="MRP Declaration",
                status="REVIEW",
                severity="CRITICAL",
                detected_value=None,
                expected="Maximum Retail Price (MRP) in INR inclusive of all taxes",
                confidence=facts.overall_confidence,
                reason="MRP not detected, but overall image confidence is below 0.80; manual review required.",
                evidence=evidence,
                legal_source=legal_source
            )

    effective_conf = conf if conf is not None else facts.overall_confidence

    if effective_conf < CONFIDENCE_FIELD_THRESHOLD:
        return CheckResult(
            check_id="CHK-03",
            rule_name="MRP Declaration",
            status="REVIEW",
            severity="CRITICAL",
            detected_value=raw_text or str(val),
            expected="Maximum Retail Price (MRP) in INR inclusive of all taxes",
            confidence=effective_conf,
            reason=f"MRP detected, but confidence ({effective_conf:.2f}) is below 0.70 threshold.",
            evidence=evidence,
            legal_source=legal_source
        )

    # Extract amount and tax inclusion
    amount: Optional[float] = None
    includes_tax: bool = True
    tax_text: Optional[str] = None

    if isinstance(val, dict):
        amount = val.get("amount")
        includes_tax = val.get("includes_tax", True)
        tax_text = val.get("tax_declaration_text")
    else:
        amount = getattr(val, "amount", None)
        includes_tax = getattr(val, "includes_tax", True)
        tax_text = getattr(val, "tax_declaration_text", None)

    detected_display = raw_text or f"Rs. {amount}"

    if amount is None or float(amount) <= 0:
        return CheckResult(
            check_id="CHK-03",
            rule_name="MRP Declaration",
            status="FAIL",
            severity="CRITICAL",
            detected_value=detected_display,
            expected="Positive MRP numeric amount",
            confidence=effective_conf,
            reason=f"MRP amount ({amount}) must be a positive number.",
            evidence=evidence,
            legal_source=legal_source
        )

    if not includes_tax:
        return CheckResult(
            check_id="CHK-03",
            rule_name="MRP Declaration",
            status="FAIL",
            severity="CRITICAL",
            detected_value=detected_display,
            expected="MRP declaration with 'inclusive of all taxes' phrase",
            confidence=effective_conf,
            reason="MRP declaration must state 'inclusive of all taxes' or 'incl. of all taxes' under Rule 2(m).",
            evidence=evidence,
            legal_source=legal_source
        )

    return CheckResult(
        check_id="CHK-03",
        rule_name="MRP Declaration",
        status="PASS",
        severity="CRITICAL",
        detected_value=detected_display,
        expected="Maximum Retail Price (MRP) in INR inclusive of all taxes",
        confidence=effective_conf,
        reason=f"MRP declared in compliant format ({detected_display}) inclusive of all taxes.",
        evidence=evidence,
        legal_source=legal_source
    )


# ==============================================================================
# CHK-04: Manufacturer / Packer / Importer Information (Rule 6(1)(a), Rule 10)
# ==============================================================================
def check_manufacturer(
    facts: StructuredFacts,
    legal_source: Optional[LegalSource] = None
) -> CheckResult:
    """
    Validates name and address of manufacturer, packer, or importer under Rule 6(1)(a) and Rule 10.
    """
    mfg_field = facts.fields.manufacturer
    pkr_field = facts.fields.packer
    imp_field = facts.fields.importer

    # Select the first available entity field
    active_field = mfg_field or pkr_field or imp_field
    val, conf, raw_text, bbox = _extract_field_helper(active_field)
    evidence = Evidence(raw_text=raw_text, bounding_box=bbox) if active_field else None

    # Missing check
    if active_field is None or val is None:
        if facts.overall_confidence >= CONFIDENCE_IMAGE_FAIL_THRESHOLD:
            return CheckResult(
                check_id="CHK-04",
                rule_name="Manufacturer/Packer/Importer Information",
                status="FAIL",
                severity="CRITICAL",
                detected_value=None,
                expected="Name and complete address of manufacturer, packer, or importer",
                confidence=facts.overall_confidence,
                reason="Name and complete address of manufacturer, packer, or importer is missing.",
                evidence=evidence,
                legal_source=legal_source
            )
        else:
            return CheckResult(
                check_id="CHK-04",
                rule_name="Manufacturer/Packer/Importer Information",
                status="REVIEW",
                severity="CRITICAL",
                detected_value=None,
                expected="Name and complete address of manufacturer, packer, or importer",
                confidence=facts.overall_confidence,
                reason="Manufacturer/packer details not detected, but overall image confidence is below 0.80; manual review required.",
                evidence=evidence,
                legal_source=legal_source
            )

    effective_conf = conf if conf is not None else facts.overall_confidence

    if effective_conf < CONFIDENCE_FIELD_THRESHOLD:
        return CheckResult(
            check_id="CHK-04",
            rule_name="Manufacturer/Packer/Importer Information",
            status="REVIEW",
            severity="CRITICAL",
            detected_value=raw_text or str(val),
            expected="Name and complete address of manufacturer, packer, or importer",
            confidence=effective_conf,
            reason=f"Manufacturer/packer details detected, but confidence ({effective_conf:.2f}) is below 0.70 threshold.",
            evidence=evidence,
            legal_source=legal_source
        )

    # Extract name and address
    name: Optional[str] = None
    address: Optional[str] = None

    if isinstance(val, dict):
        name = val.get("name")
        address = val.get("address")
    else:
        name = getattr(val, "name", None)
        address = getattr(val, "address", None)

    detected_display = raw_text or f"{name}, {address}"

    if not name or not str(name).strip():
        return CheckResult(
            check_id="CHK-04",
            rule_name="Manufacturer/Packer/Importer Information",
            status="FAIL",
            severity="CRITICAL",
            detected_value=detected_display,
            expected="Entity name (manufacturer, packer, or importer)",
            confidence=effective_conf,
            reason="Manufacturer/packer name is missing.",
            evidence=evidence,
            legal_source=legal_source
        )

    if not address or len(str(address).strip()) < 3:
        return CheckResult(
            check_id="CHK-04",
            rule_name="Manufacturer/Packer/Importer Information",
            status="FAIL",
            severity="CRITICAL",
            detected_value=detected_display,
            expected="Complete postal address with city/state/PIN",
            confidence=effective_conf,
            reason="Manufacturer/packer address is missing or incomplete.",
            evidence=evidence,
            legal_source=legal_source
        )

    return CheckResult(
        check_id="CHK-04",
        rule_name="Manufacturer/Packer/Importer Information",
        status="PASS",
        severity="CRITICAL",
        detected_value=detected_display,
        expected="Name and complete address of manufacturer, packer, or importer",
        confidence=effective_conf,
        reason=f"Manufacturer/packer declared with name ('{name}') and address ('{address}').",
        evidence=evidence,
        legal_source=legal_source
    )


# ==============================================================================
# CHK-05: Manufacturing / Packing Date Declaration (Rule 6(1)(d))
# ==============================================================================
def check_manufacturing_date(
    facts: StructuredFacts,
    legal_source: Optional[LegalSource] = None
) -> CheckResult:
    """
    Validates month and year of manufacture or pre-packing under Rule 6(1)(d).
    """
    field = facts.fields.manufacturing_date
    val, conf, raw_text, bbox = _extract_field_helper(field)
    evidence = Evidence(raw_text=raw_text, bounding_box=bbox) if field else None

    # Missing check
    if val is None:
        if facts.overall_confidence >= CONFIDENCE_IMAGE_FAIL_THRESHOLD:
            return CheckResult(
                check_id="CHK-05",
                rule_name="Manufacturing/Packing Date Declaration",
                status="FAIL",
                severity="HIGH",
                detected_value=None,
                expected="Month and year of manufacture or pre-packing",
                confidence=facts.overall_confidence,
                reason="Month and year of manufacture or pre-packing is missing.",
                evidence=evidence,
                legal_source=legal_source
            )
        else:
            return CheckResult(
                check_id="CHK-05",
                rule_name="Manufacturing/Packing Date Declaration",
                status="REVIEW",
                severity="HIGH",
                detected_value=None,
                expected="Month and year of manufacture or pre-packing",
                confidence=facts.overall_confidence,
                reason="Manufacturing date not detected, but overall image confidence is below 0.80; manual review required.",
                evidence=evidence,
                legal_source=legal_source
            )

    effective_conf = conf if conf is not None else facts.overall_confidence

    if effective_conf < CONFIDENCE_FIELD_THRESHOLD:
        return CheckResult(
            check_id="CHK-05",
            rule_name="Manufacturing/Packing Date Declaration",
            status="REVIEW",
            severity="HIGH",
            detected_value=raw_text or str(val),
            expected="Month and year of manufacture or pre-packing",
            confidence=effective_conf,
            reason=f"Manufacturing date detected, but confidence ({effective_conf:.2f}) is below 0.70 threshold.",
            evidence=evidence,
            legal_source=legal_source
        )

    month: Optional[int] = None
    year: Optional[int] = None

    if isinstance(val, dict):
        month = val.get("month")
        year = val.get("year")
    else:
        month = getattr(val, "month", None)
        year = getattr(val, "year", None)

    detected_display = raw_text or f"{month:02d}/{year}" if (month and year) else str(val)

    if month is None or not (1 <= int(month) <= 12):
        return CheckResult(
            check_id="CHK-05",
            rule_name="Manufacturing/Packing Date Declaration",
            status="FAIL",
            severity="HIGH",
            detected_value=detected_display,
            expected="Valid month between 1 and 12",
            confidence=effective_conf,
            reason=f"Invalid manufacturing month: {month}. Must be between 1 and 12.",
            evidence=evidence,
            legal_source=legal_source
        )

    if year is None or int(year) < 2000 or int(year) > 2035:
        return CheckResult(
            check_id="CHK-05",
            rule_name="Manufacturing/Packing Date Declaration",
            status="FAIL",
            severity="HIGH",
            detected_value=detected_display,
            expected="Plausible manufacturing year",
            confidence=effective_conf,
            reason=f"Invalid or implausible manufacturing year: {year}.",
            evidence=evidence,
            legal_source=legal_source
        )

    return CheckResult(
        check_id="CHK-05",
        rule_name="Manufacturing/Packing Date Declaration",
        status="PASS",
        severity="HIGH",
        detected_value=detected_display,
        expected="Month and year of manufacture or pre-packing",
        confidence=effective_conf,
        reason=f"Month and year of manufacture/packing declared ({int(month):02d}/{year}).",
        evidence=evidence,
        legal_source=legal_source
    )


# ==============================================================================
# CHK-06: Consumer Care Information (Rule 6(2))
# ==============================================================================
def check_consumer_care(
    facts: StructuredFacts,
    legal_source: Optional[LegalSource] = None
) -> CheckResult:
    """
    Validates consumer grievance contact details (phone, email, address) under Rule 6(2).
    """
    field = facts.fields.consumer_care
    val, conf, raw_text, bbox = _extract_field_helper(field)
    evidence = Evidence(raw_text=raw_text, bounding_box=bbox) if field else None

    # Missing check
    if val is None:
        if facts.overall_confidence >= CONFIDENCE_IMAGE_FAIL_THRESHOLD:
            return CheckResult(
                check_id="CHK-06",
                rule_name="Consumer Care Information",
                status="FAIL",
                severity="HIGH",
                detected_value=None,
                expected="Name, telephone, email, or address for consumer complaints",
                confidence=facts.overall_confidence,
                reason="Consumer care details for grievance redressal are missing.",
                evidence=evidence,
                legal_source=legal_source
            )
        else:
            return CheckResult(
                check_id="CHK-06",
                rule_name="Consumer Care Information",
                status="REVIEW",
                severity="HIGH",
                detected_value=None,
                expected="Name, telephone, email, or address for consumer complaints",
                confidence=facts.overall_confidence,
                reason="Consumer care details not detected, but overall image confidence is below 0.80; manual review required.",
                evidence=evidence,
                legal_source=legal_source
            )

    effective_conf = conf if conf is not None else facts.overall_confidence

    if effective_conf < CONFIDENCE_FIELD_THRESHOLD:
        return CheckResult(
            check_id="CHK-06",
            rule_name="Consumer Care Information",
            status="REVIEW",
            severity="HIGH",
            detected_value=raw_text or str(val),
            expected="Name, telephone, email, or address for consumer complaints",
            confidence=effective_conf,
            reason=f"Consumer care details detected, but confidence ({effective_conf:.2f}) is below 0.70 threshold.",
            evidence=evidence,
            legal_source=legal_source
        )

    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

    if isinstance(val, dict):
        phone = val.get("phone")
        email = val.get("email")
        address = val.get("address")
    else:
        phone = getattr(val, "phone", None)
        email = getattr(val, "email", None)
        address = getattr(val, "address", None)

    channels = []
    if phone and str(phone).strip():
        channels.append(f"phone: {phone}")
    if email and str(email).strip():
        channels.append(f"email: {email}")
    if address and str(address).strip():
        channels.append(f"address: {address}")

    detected_display = raw_text or (", ".join(channels) if channels else str(val))

    if not channels:
        return CheckResult(
            check_id="CHK-06",
            rule_name="Consumer Care Information",
            status="FAIL",
            severity="HIGH",
            detected_value=detected_display,
            expected="Telephone number, email, or postal address for consumer complaints",
            confidence=effective_conf,
            reason="Consumer care declaration must provide telephone number, email, or contact address.",
            evidence=evidence,
            legal_source=legal_source
        )

    return CheckResult(
        check_id="CHK-06",
        rule_name="Consumer Care Information",
        status="PASS",
        severity="HIGH",
        detected_value=detected_display,
        expected="Name, telephone, email, or address for consumer complaints",
        confidence=effective_conf,
        reason=f"Consumer care contact information declared ({', '.join(channels)}).",
        evidence=evidence,
        legal_source=legal_source
    )


# ==============================================================================
# Mapping of Core Active MVP Checks
# ==============================================================================
CORE_CHECKS = {
    "CHK-01": check_product_name,
    "CHK-02": check_net_quantity,
    "CHK-03": check_mrp,
    "CHK-04": check_manufacturer,
    "CHK-05": check_manufacturing_date,
    "CHK-06": check_consumer_care,
}

# Future stretch checks explicitly documented and deferred post-MVP:
# CHK-07: Prohibited quantity qualifiers under Rule 12(6)
# CHK-09: Country of Origin declaration for imported products under Rule 6(1)(a) proviso / Rule 10
STRETCH_CHECKS = ["CHK-07", "CHK-09"]
