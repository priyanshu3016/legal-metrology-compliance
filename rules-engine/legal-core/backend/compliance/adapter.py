"""
Adapter module: Bridges Person 5 (AI / OCR Engine) to Person 6 (Compliance Rules Engine).

Transforms the multi-image analysis output dictionary from Person 5's
`analyze_multi_image()` into canonical `StructuredFacts` expected by
Person 6's `run_compliance_checks()`.
"""

import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from backend.compliance.schemas import (
    StructuredFacts,
    FactFields,
    ExtractedField,
    BoundingBox,
    NetQuantityValue,
    MRPValue,
    ManufacturerValue,
    DateValue,
    ConsumerCareValue,
)


def polygon_to_bbox(polygon: Optional[list]) -> Optional[BoundingBox]:
    """
    Converts Person 5's 4-point polygon [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    to Person 6's axis-aligned BoundingBox(x, y, width, height).
    """
    if not polygon or len(polygon) < 4:
        return None
    try:
        xs = [pt[0] for pt in polygon]
        ys = [pt[1] for pt in polygon]
        min_x = int(round(min(xs)))
        max_x = int(round(max(xs)))
        min_y = int(round(min(ys)))
        max_y = int(round(max(ys)))
        return BoundingBox(
            x=min_x,
            y=min_y,
            width=max(0, max_x - min_x),
            height=max(0, max_y - min_y)
        )
    except (IndexError, TypeError, ValueError):
        return None


def parse_net_quantity_str(val_str: Optional[str]) -> Optional[NetQuantityValue]:
    """
    Parses normalized quantity string (e.g. '30.5 g', '200 g', '1.5 l') into NetQuantityValue.
    """
    if not val_str:
        return None
    # Match numeric portion followed by unit
    m = re.search(r'([\d\.]+)\s*([a-zA-Z]+)', val_str.strip())
    if m:
        try:
            numeric_val = float(m.group(1))
            unit_val = m.group(2).lower()
            return NetQuantityValue(numeric=numeric_val, unit=unit_val)
        except ValueError:
            pass
    return None


def parse_mrp_str(
    val_str: Optional[str],
    raw_match: Optional[str] = None,
    full_text: str = ""
) -> Optional[MRPValue]:
    """
    Parses MRP numeric string (e.g. '10', '120.00') and checks for mandatory tax declaration.
    """
    if not val_str:
        return None
    # Strip any stray non-numeric symbols
    cleaned = re.sub(r'[^\d\.]', '', val_str)
    if not cleaned:
        return None
    try:
        amount = float(cleaned)
    except ValueError:
        return None

    # Check for tax inclusion phrasing in raw match or packaging raw text
    combined_text = f"{raw_match or ''} {full_text}".lower()
    tax_phrases = [
        "incl. of all taxes",
        "inclusive of all taxes",
        "incl of all taxes",
        "incl. of taxes",
        "inclusive of taxes",
        "incl of taxes",
        "all taxes incl",
    ]
    includes_tax = any(phrase in combined_text for phrase in tax_phrases)
    tax_decl_text = "incl. of all taxes" if includes_tax else None

    return MRPValue(
        amount=amount,
        currency="INR",
        includes_tax=includes_tax,
        tax_declaration_text=tax_decl_text
    )


def parse_date_str(val_str: Optional[str]) -> Optional[DateValue]:
    """
    Parses manufacturing date string (e.g. '03/AUG/26', '25/08/26', '08/2026', '05/2026').
    """
    if not val_str:
        return None

    cleaned = val_str.strip().upper()

    month_map = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
    }

    # 1. Format with named month: e.g. '03/AUG/26', '25-AUG-2026', 'AUG 2026'
    for mon_name, mon_num in month_map.items():
        if mon_name in cleaned:
            # Find year digits
            year_matches = re.findall(r'\b\d{2,4}\b', cleaned)
            for ym in reversed(year_matches):
                y = int(ym)
                if y < 100:
                    y += 2000
                if 2000 <= y <= 2035:
                    return DateValue(month=mon_num, year=y, format="MON/YYYY")

    # 2. Format with all numeric parts: DD/MM/YYYY, MM/YYYY, DD/MM/YY, MM/YY
    parts = re.findall(r'\d+', cleaned)
    if len(parts) >= 2:
        if len(parts) >= 3:
            # Assume DD/MM/YYYY or YYYY/MM/DD
            if len(parts[0]) == 4:
                year = int(parts[0])
                month = int(parts[1])
            else:
                month = int(parts[1])
                year = int(parts[2])
        else:
            # Assume MM/YYYY or MM/YY
            month = int(parts[0])
            year = int(parts[1])

        if year < 100:
            year += 2000

        if 1 <= month <= 12 and 2000 <= year <= 2035:
            return DateValue(month=month, year=year, format="MM/YYYY")

    return None


def parse_consumer_care_str(val_str: Optional[str]) -> Optional[ConsumerCareValue]:
    """
    Extracts phone and email from Person 5's pipe-separated consumer care string:
    e.g. '1800 2583333 | customercare@amul.coop' or '1800 22 4020 | CONSUMER.FEEDBACK@PEPSICO.COM'.
    """
    if not val_str:
        return None

    phone: Optional[str] = None
    email: Optional[str] = None

    # Check for email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', val_str)
    if email_match:
        email = email_match.group(0).strip()

    # Check for phone number (toll-free 1800..., or 10-digit number)
    phone_match = re.search(r'(?:1800[\s\d\-]{6,12}|\b\d{10}\b|\+91[\s\d\-]{10,13})', val_str)
    if phone_match:
        phone = phone_match.group(0).strip()

    # If neither regex matched, treat entire string as general contact info
    if not phone and not email:
        return ConsumerCareValue(phone=None, email=None, address=val_str.strip())

    return ConsumerCareValue(phone=phone, email=email, address=None)


def parse_manufacturer_str(val_str: Optional[str]) -> Optional[ManufacturerValue]:
    """
    Parses manufacturer string into name and postal address.
    e.g. "Kaira District Co-operative Milk Producers'Union Ltd., Anand-388 001, India."
    """
    if not val_str or not val_str.strip():
        return None

    cleaned = val_str.strip()
    # Split by comma into name (first segment) and address (remainder)
    parts = cleaned.split(",", 1)
    if len(parts) == 2:
        name = parts[0].strip()
        address = parts[1].strip()
    else:
        name = cleaned
        address = cleaned

    return ManufacturerValue(name=name, address=address, role="manufacturer")


def ai_result_to_structured_facts(
    ai_result: Dict[str, Any],
    inspection_id: Optional[str] = None
) -> StructuredFacts:
    """
    Converts Person 5's analyze_multi_image output dictionary into Person 6's StructuredFacts.

    Args:
        ai_result: Dictionary returned by Person 5's analyze_multi_image() or analyze_image().
        inspection_id: Optional custom identifier.

    Returns:
        StructuredFacts instance ready for run_compliance_checks().
    """
    detections = ai_result.get("detections", [])
    det_map: Dict[str, Dict[str, Any]] = {d["field"]: d for d in detections if "field" in d}

    # Aggregate full raw text across views
    raw_texts: List[str] = []
    raw_ocr = ai_result.get("raw_ocr") or {}
    for view in ["front", "back", "side"]:
        view_data = raw_ocr.get(view)
        if view_data and isinstance(view_data, dict) and view_data.get("full_text"):
            raw_texts.append(view_data["full_text"])
    full_text = "\n".join(raw_texts)

    # Compute overall confidence
    confidences = [
        d["confidence"] for d in detections
        if d.get("status") in ("found", "low_confidence") and d.get("confidence", 0) > 0
    ]
    if confidences:
        overall_conf = round(sum(confidences) / len(confidences), 4)
    else:
        # Fallback to OCR averages if detections were not found
        ocr_confs = []
        for view in ["front", "back", "side"]:
            v = raw_ocr.get(view)
            if v and isinstance(v, dict) and v.get("avg_confidence"):
                ocr_confs.append(v["avg_confidence"])
        overall_conf = round(sum(ocr_confs) / len(ocr_confs), 4) if ocr_confs else 0.85

    # 1. Product Name (CHK-01)
    d_name = det_map.get("product_name")
    field_product_name = None
    if d_name and d_name.get("status") != "not_found" and d_name.get("value"):
        field_product_name = ExtractedField(
            value=d_name["value"],
            confidence=d_name.get("confidence"),
            raw_text=d_name.get("raw_match") or d_name["value"],
            bounding_box=polygon_to_bbox(d_name.get("bbox"))
        )

    # 2. Net Quantity (CHK-02)
    d_qty = det_map.get("net_quantity")
    field_net_qty = None
    if d_qty and d_qty.get("status") != "not_found" and d_qty.get("value"):
        qty_val = parse_net_quantity_str(d_qty["value"])
        if qty_val:
            field_net_qty = ExtractedField(
                value=qty_val,
                confidence=d_qty.get("confidence"),
                raw_text=d_qty.get("raw_match") or d_qty["value"],
                bounding_box=polygon_to_bbox(d_qty.get("bbox"))
            )

    # 3. MRP (CHK-03)
    d_mrp = det_map.get("mrp")
    field_mrp = None
    if d_mrp and d_mrp.get("status") != "not_found" and d_mrp.get("value"):
        mrp_val = parse_mrp_str(d_mrp["value"], d_mrp.get("raw_match"), full_text)
        if mrp_val:
            field_mrp = ExtractedField(
                value=mrp_val,
                confidence=d_mrp.get("confidence"),
                raw_text=d_mrp.get("raw_match") or f"MRP Rs. {d_mrp['value']}",
                bounding_box=polygon_to_bbox(d_mrp.get("bbox"))
            )

    # 4. Manufacturer / Packer / Importer (CHK-04)
    d_mfg = det_map.get("manufacturer_packer_importer")
    field_mfg = None
    if d_mfg and d_mfg.get("status") != "not_found" and d_mfg.get("value"):
        mfg_val = parse_manufacturer_str(d_mfg["value"])
        if mfg_val:
            field_mfg = ExtractedField(
                value=mfg_val,
                confidence=d_mfg.get("confidence"),
                raw_text=d_mfg.get("raw_match") or d_mfg["value"],
                bounding_box=polygon_to_bbox(d_mfg.get("bbox"))
            )

    # 5. Manufacturing Date (CHK-05)
    d_date = det_map.get("manufacturing_date")
    field_date = None
    if d_date and d_date.get("status") != "not_found" and d_date.get("value"):
        date_val = parse_date_str(d_date["value"])
        if date_val:
            field_date = ExtractedField(
                value=date_val,
                confidence=d_date.get("confidence"),
                raw_text=d_date.get("raw_match") or d_date["value"],
                bounding_box=polygon_to_bbox(d_date.get("bbox"))
            )

    # 6. Consumer Care (CHK-06)
    d_care = det_map.get("consumer_care")
    field_care = None
    if d_care and d_care.get("status") != "not_found" and d_care.get("value"):
        care_val = parse_consumer_care_str(d_care["value"])
        if care_val:
            field_care = ExtractedField(
                value=care_val,
                confidence=d_care.get("confidence"),
                raw_text=d_care.get("raw_match") or d_care["value"],
                bounding_box=polygon_to_bbox(d_care.get("bbox"))
            )

    # 7. Country of Origin (Stretch CHK-09)
    d_origin = det_map.get("country_of_origin")
    field_origin = None
    if d_origin and d_origin.get("status") != "not_found" and d_origin.get("value"):
        field_origin = ExtractedField(
            value=d_origin["value"],
            confidence=d_origin.get("confidence"),
            raw_text=d_origin.get("raw_match") or d_origin["value"],
            bounding_box=polygon_to_bbox(d_origin.get("bbox"))
        )

    fields = FactFields(
        product_name=field_product_name,
        net_quantity=field_net_qty,
        mrp=field_mrp,
        manufacturer=field_mfg,
        packer=None,
        importer=None,
        manufacturing_date=field_date,
        consumer_care=field_care,
        country_of_origin=field_origin
    )

    # Image quality heuristic from overall confidence
    image_quality = "good" if overall_conf >= 0.75 else ("fair" if overall_conf >= 0.60 else "poor")

    # Generate unique inspection ID if not passed
    insp_id = inspection_id or ai_result.get("image_id") or f"insp-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    return StructuredFacts(
        inspection_id=insp_id,
        overall_confidence=overall_conf,
        image_quality=image_quality,
        raw_text=full_text,
        fields=fields,
        quantity_qualifiers_detected=[],
        is_imported_hint=bool(field_origin and field_origin.value and str(field_origin.value).strip().lower() != "india")
    )
