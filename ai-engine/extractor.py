"""
Field Extraction Module for Legal Metrology Declarations.
Applies deterministic regex, keyword matching, and heuristics to parsed OCR results.
"""

import re
from typing import List, Dict, Any, Optional, Tuple

from config import (
    FIELD_MRP,
    FIELD_NET_QUANTITY,
    FIELD_COUNTRY_OF_ORIGIN,
    FIELD_BEST_BEFORE,
    FIELD_MFG_DATE,
    FIELD_PRODUCT_NAME,
    FIELD_MANUFACTURER,
    FIELD_CONSUMER_CARE,
    FIELD_UNIT_SALE_PRICE,
    MANDATORY_FIELDS,
    DETECTION_CONFIDENCE_THRESHOLD
)
from schemas import (
    create_detection,
    create_empty_detection,
    STATUS_AMBIGUOUS,
    STATUS_FOUND,
    STATUS_LOW_CONFIDENCE
)



def compute_bbox_union(bboxes: List[List[List[float]]]) -> Optional[List[List[float]]]:
    """
    Compute the bounding box union enclosing all given 4-point polygon bboxes.
    Returns standard 4-point rectangle: [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]].
    """
    if not bboxes:
        return None

    all_x = []
    all_y = []
    for bbox in bboxes:
        if bbox and len(bbox) == 4:
            for pt in bbox:
                all_x.append(pt[0])
                all_y.append(pt[1])

    if not all_x or not all_y:
        return None

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    return [
        [round(min_x, 1), round(min_y, 1)],
        [round(max_x, 1), round(min_y, 1)],
        [round(max_x, 1), round(max_y, 1)],
        [round(min_x, 1), round(max_y, 1)]
    ]


# =========================================================================
# 1. Maximum Retail Price (MRP) Extractor
# =========================================================================

MRP_PATTERNS = [
    # MRP Rs. 20.00 / M.R.P. ₹ 120 / MRP: 120
    re.compile(
        r"(?:M\.?\s*R\.?\s*P\.?|Maximum\s*Retail\s*Price)\s*[:\.]?\s*(?:Rs\.?|INR|[₹?])?\s*(\d+(?:[.,]\d{1,2})?)",
        re.IGNORECASE
    ),
    # Rs. 120.00 or ₹ 120 (when word MRP or Price is nearby)
    re.compile(
        r"(?:MRP|Price)[^0-9\n]{0,20}(?:Rs\.?|INR|[₹?])\s*(\d+(?:[.,]\d{1,2})?)",
        re.IGNORECASE
    ),
    # Standalone ₹ 120.00
    re.compile(
        r"[₹]\s*(\d+(?:[.,]\d{1,2})?)",
        re.IGNORECASE
    )
]


def extract_mrp(ocr_results: List[Dict[str, Any]], full_text: str) -> Optional[Dict[str, Any]]:
    """Extract Maximum Retail Price from OCR text lines."""
    for item in ocr_results:
        line_text = item["text"]
        for pattern in MRP_PATTERNS:
            match = pattern.search(line_text)
            if match:
                raw_num = match.group(1).replace(",", ".")
                try:
                    num_val = float(raw_num)
                    val_str = f"{num_val:.2f}" if "." in raw_num else str(int(num_val))
                    return create_detection(
                        field_name=FIELD_MRP,
                        value=val_str,
                        raw_match=line_text,
                        confidence=item["confidence"],
                        bbox=item["bbox"]
                    )
                except ValueError:
                    continue
    return None


# =========================================================================
# 2. Net Quantity Extractor
# =========================================================================

UNIT_NORMALIZATION = {
    "gm": "g", "gms": "g", "gram": "g", "grams": "g", "g": "g",
    "kg": "kg", "kgs": "kg", "kilo": "kg", "kilogram": "kg",
    "ml": "ml", "mls": "ml", "millilitre": "ml", "milliliter": "ml",
    "l": "l", "ltr": "l", "litre": "l", "liter": "l",
    "pcs": "pcs", "piece": "pcs", "pieces": "pcs", "units": "units", "nos": "nos"
}

PROMO_NET_QTY_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)\s*\(\s*\d+(?:[.,]\d+)?\s*[a-zA-Z]+\s*\+\s*\d+(?:[.,]\d+)?\s*[a-zA-Z]+\s*\)",
    re.IGNORECASE
)

NET_QTY_PATTERNS = [
    # Net Wt: 100g / Net Qty: 1.5 L / Net Weight 500 g / Net Volume: 750 mL
    re.compile(
        r"(?:Net\s*(?:Wt\.?|Weight|Qty\.?|Quantity|Content|Contents|Vol\.?|Volume)?)\s*[:\.]?\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)\b",
        re.IGNORECASE
    ),
    # Weight: 100g / Volume: 750 ml
    re.compile(
        r"(?:Weight|Quantity|Volume)\s*[:\.]?\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)\b",
        re.IGNORECASE
    )
]


def extract_net_quantity(ocr_results: List[Dict[str, Any]], full_text: str) -> Optional[Dict[str, Any]]:
    """Extract Net Quantity and standardized unit."""
    # Priority 1: Explicit Net Quantity / Net Weight declarations
    for item in ocr_results:
        line_text = item["text"]
        for pattern in NET_QTY_PATTERNS:
            match = pattern.search(line_text)
            if match:
                amount_str = match.group(1).replace(",", ".")
                raw_unit = match.group(2).lower()

                normalized_unit = UNIT_NORMALIZATION.get(raw_unit)
                if normalized_unit:
                    value = f"{amount_str} {normalized_unit}"
                    return create_detection(
                        field_name=FIELD_NET_QUANTITY,
                        value=value,
                        raw_match=line_text,
                        confidence=item["confidence"],
                        bbox=item["bbox"]
                    )

    # Priority 2: Standalone promotional net weight declaration (e.g. "30.5 g (28 g+2.5 g)")
    for item in ocr_results:
        line_text = item["text"]
        match = PROMO_NET_QTY_PATTERN.search(line_text)
        if match:
            amount_str = match.group(1).replace(",", ".")
            raw_unit = match.group(2).lower()
            normalized_unit = UNIT_NORMALIZATION.get(raw_unit)
            if normalized_unit:
                value = f"{amount_str} {normalized_unit}"
                return create_detection(
                    field_name=FIELD_NET_QUANTITY,
                    value=value,
                    raw_match=line_text,
                    confidence=item["confidence"],
                    bbox=item["bbox"]
                )
    return None


# =========================================================================
# 3. Country of Origin Extractor
# =========================================================================

COUNTRY_PATTERNS = [
    re.compile(r"(?:Country\s*of\s*Origin|Made\s*in|Product\s*of)\s*[:\.]?\s*([A-Za-z\s]+)", re.IGNORECASE),
    re.compile(r"\bOrigin\s*[:\.]?\s*([A-Za-z\s]+)", re.IGNORECASE)
]

COMMON_COUNTRIES = ["india", "china", "usa", "germany", "japan", "thailand", "vietnam", "taiwan", "indonesia", "malaysia"]


def extract_country_of_origin(ocr_results: List[Dict[str, Any]], full_text: str) -> Optional[Dict[str, Any]]:
    """Extract Country of Origin."""
    for item in ocr_results:
        line_text = item["text"]
        for pattern in COUNTRY_PATTERNS:
            match = pattern.search(line_text)
            if match:
                country_candidate = match.group(1).strip().split(",")[0].split(".")[0].strip()
                # Typo normalization (e.g. OCR misreading capital 'I' as lowercase 'l' in 'lndia')
                if country_candidate.lower() in ("lndia", "1ndia"):
                    country_candidate = "India"
                else:
                    country_candidate = country_candidate.title()

                if len(country_candidate) >= 3:
                    return create_detection(
                        field_name=FIELD_COUNTRY_OF_ORIGIN,
                        value=country_candidate,
                        raw_match=line_text,
                        confidence=item["confidence"],
                        bbox=item["bbox"]
                    )

    # Fallback: check if "Made in India" exists anywhere
    for item in ocr_results:
        if "made in india" in item["text"].lower():
            return create_detection(
                field_name=FIELD_COUNTRY_OF_ORIGIN,
                value="India",
                raw_match=item["text"],
                confidence=item["confidence"],
                bbox=item["bbox"]
            )

    return None


# =========================================================================
# 4. Manufacturing / Packing Date Extractor
# =========================================================================

JOINT_MFD_USE_BY_PATTERN = re.compile(
    r"(\d{1,2}[\/\-\.](?:[a-zA-Z]{3,9}|\d{1,2})[\/\-\.]\d{2,4})\s*(?:&|and)\s*(\d{1,2}[\/\-\.](?:[a-zA-Z]{3,9}|\d{1,2})[\/\-\.]\d{2,4})",
    re.IGNORECASE
)
JOINT_HEADER_KEYWORD_PATTERN = re.compile(
    r"(?:Mfg\.?|Mfd\.?|Packed|Pkg\.?|DOM)\s*(?:&|and)\s*(?:Use\s*By|Best\s*Before|Exp\.?)",
    re.IGNORECASE
)

MFG_PATTERNS = [
    # Mfg Date: 03/2026 / Mfd: 15-08-2025 / Packed: Mar 2026 / Packed on: Mar 2026 / PKD:03/AUG/26 / MFD:03/AUG/26
    re.compile(
        r"(?:Mfg\.?|Mfd\.?|Pkd\.?|Packed|Pkg\.?|DOM|Manufacturing)\s*(?:Date|Dt\.?|D|on)?\s*[:\.]?\s*([0-9A-Za-z\/\-\.\s]{4,15})",
        re.IGNORECASE
    ),
    re.compile(
        r"(?:Date\s*of\s*(?:Manufacture|Packing))\s*[:\.]?\s*([0-9A-Za-z\/\-\.\s]{4,15})",
        re.IGNORECASE
    )
]


def extract_manufacturing_date(ocr_results: List[Dict[str, Any]], full_text: str) -> Optional[Dict[str, Any]]:
    """Extract Manufacturing or Packing Date."""
    # Priority 1: Joint MFD & USE BY declarations (e.g. MFD & USE BY: 25/08/26 & 07/01/27)
    has_joint_header = any(JOINT_HEADER_KEYWORD_PATTERN.search(item["text"]) for item in ocr_results)
    for item in ocr_results:
        line_text = item["text"]
        if has_joint_header or JOINT_HEADER_KEYWORD_PATTERN.search(line_text):
            m = JOINT_MFD_USE_BY_PATTERN.search(line_text)
            if m:
                date_val = m.group(1).strip()
                return create_detection(
                    field_name=FIELD_MFG_DATE,
                    value=date_val,
                    raw_match=line_text,
                    confidence=item["confidence"],
                    bbox=item["bbox"]
                )

    # Priority 2: Standard standalone manufacturing date patterns
    for item in ocr_results:
        line_text = item["text"]
        for pattern in MFG_PATTERNS:
            match = pattern.search(line_text)
            if match:
                date_val = match.group(1).strip().strip(".,;")
                # Clean up excess text
                date_val = re.sub(r"\s+", " ", date_val)
                # Disqualify prose disclaimers like "see below"
                if re.search(r"\bsee\s+(?:below|pkg|pack|flap)\b", date_val, re.IGNORECASE):
                    continue
                # Extract clean date token if structured date is present
                date_match = re.search(
                    r"\b(?:\d{1,2}[\/\-\.](?:[a-zA-Z]{3,9}|\d{1,2})[\/\-\.]\d{2,4}|(?:[a-zA-Z]{3,9})\s*\d{2,4}|\d{1,2}[\/\-\.]\d{2,4})\b",
                    date_val
                )
                if date_match:
                    date_val = date_match.group(0)

                # Verify it looks like a date (contains digits)
                if any(ch.isdigit() for ch in date_val) and len(date_val) >= 4:
                    return create_detection(
                        field_name=FIELD_MFG_DATE,
                        value=date_val,
                        raw_match=line_text,
                        confidence=item["confidence"],
                        bbox=item["bbox"]
                    )
    return None


# =========================================================================
# 5. Best Before / Use By Extractor
# =========================================================================

BEST_BEFORE_PATTERNS = [
    # Best Before 12 months / Best Before: 31/12/2026 / Use By 05/2026 / Exp Date: 10/2026 / EXP:03/AUG/27
    re.compile(
        r"(?:Best\s*(?:Before|By)|Use\s*(?:By|Before)|Expiry\s*(?:Date|Dt)?|Exp\.?\s*(?:Date|Dt)?)\s*[:\.]?\s*([0-9A-Za-z\/\-\.\s]{3,35})",
        re.IGNORECASE
    ),
    # Shelf life 6 months from manufacture
    re.compile(
        r"(?:Shelf\s*Life)\s*[:\.]?\s*([0-9A-Za-z\/\-\.\s]{3,35})",
        re.IGNORECASE
    )
]


def _is_valid_best_before_value(val: str) -> bool:
    """Validate that the extracted value contains a genuine date or duration, not prose."""
    if not val or len(val) < 3:
        return False
    val_lower = val.lower().strip()

    # Reject if it's solely prose disclaimer words without a number or date
    has_duration = bool(re.search(
        r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|eighteen|twenty\s*four|thirty\s*six)\s*(?:months?|mths?|days?|years?|yrs?|weeks?|hours?|hrs?)\b",
        val_lower
    ))
    has_date = bool(re.search(
        r"\b(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}[\/\-\.](?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\/\-\.]\d{2,4}|\d{1,2}[\/\-\.]\d{4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{2,4}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{2,4})\b",
        val_lower
    ))

    return has_duration or has_date


def extract_best_before(ocr_results: List[Dict[str, Any]], full_text: str) -> Optional[Dict[str, Any]]:
    """Extract Best Before, Use By, or Expiry statement."""
    # Priority 1: Joint MFD & USE BY declarations (extract date2 as use by / best before)
    has_joint_header = any(JOINT_HEADER_KEYWORD_PATTERN.search(item["text"]) for item in ocr_results)
    for item in ocr_results:
        line_text = item["text"]
        if has_joint_header or JOINT_HEADER_KEYWORD_PATTERN.search(line_text):
            m = JOINT_MFD_USE_BY_PATTERN.search(line_text)
            if m:
                date_val = m.group(2).strip()
                return create_detection(
                    field_name=FIELD_BEST_BEFORE,
                    value=date_val,
                    raw_match=line_text,
                    confidence=item["confidence"],
                    bbox=item["bbox"]
                )

    # Priority 2: Standard best before / use by patterns
    for item in ocr_results:
        line_text = item["text"]
        for pattern in BEST_BEFORE_PATTERNS:
            match = pattern.search(line_text)
            if match:
                bb_val = match.group(1).strip().strip(".,;")
                bb_val = re.sub(r"\s+", " ", bb_val)
                if _is_valid_best_before_value(bb_val):
                    date_match = re.search(
                        r"\b(?:\d{1,2}[\/\-\.](?:[a-zA-Z]{3,9}|\d{1,2})[\/\-\.]\d{2,4}|(?:[a-zA-Z]{3,9})\s*\d{2,4}|\d{1,2}[\/\-\.]\d{2,4})\b",
                        bb_val
                    )
                    if date_match and not any(dur in bb_val.lower() for dur in ["month", "day", "year", "week"]):
                        bb_val = date_match.group(0)

                    return create_detection(
                        field_name=FIELD_BEST_BEFORE,
                        value=bb_val,
                        raw_match=line_text,
                        confidence=item["confidence"],
                        bbox=item["bbox"]
                    )
    return None


# =========================================================================
# 6. Product Name Extractor (Heuristic Prominence)
# =========================================================================

DECLARATION_KEYWORD_BLACKLIST = [
    "mrp", "m.r.p", "net wt", "net weight", "net qty", "net quantity",
    "mfg", "mfd", "pkd", "packed", "best before", "use by", "expiry", "exp",
    "country of origin", "made in", "customer care", "consumer care",
    "toll free", "manufactured", "manufac", "marketed", "mkt", "imported", "unit sale price",
    "usp", "ingredients", "nutrition", "nutritional", "allergen", "serving", "serve size",
    "batch", "b. no", "b.no", "b no", "bn:", "mdd", "lot no", "license", "lic. no", "lic no",
    "fssai", "fssat", "fssa",
    "store refrigerated", "refrigerate", "once opened", "dietary", "allowance",
    "average values", "approximate values", "cholesterol", "carbohydrate", "sodium", "protein",
    "energy", "sugar", "sugars", "fat", "kcal", "amount per", "per 100", "per pack",
    "perserving", "per serving", "rdastandsfor", "rda", "below", "call us", "email us", "nutrients"
]

DESCRIPTOR_OR_FLAVOR_BLACKLIST = [
    "magic masala", "finest potatoes", "made with", "madewith",
    "india's", "indias", "potatoes", "potato chips", "potato",
    "cream & onion", "cream and onion", "tangy tomato", "spanish tomato",
    "classic salted", "salted", "flavour", "flavor", "colour", "color",
    "farm", "fresh", "natural", "pure", "crispy", "crunchy"
]



def _is_valid_product_name(text: str) -> bool:
    """Validate candidate product name, rejecting code-like/batch/serial strings, URLs, dates, descriptors, and addresses."""
    if not text:
        return False

    raw = text.strip()
    # Reject strings with unusual leading punctuation when code-like
    if raw.startswith((":", ";", "#", "/", "\\", "=", "-", "_", "*", ".", "—", "&", "+")):
        return False

    # Reject declaration / code label prefixes and patterns (PKD:, EXP:, USP:, BN:, MRP:, MFD:, etc.)
    if re.search(r"(?i)\b(?:pkd|exp|usp|bn|mrp|mfd|mfg|batch|lot|pkg|dom)[\s:\.\/-]", raw):
        return False

    # Reject b. no / per pack patterns
    if re.search(r"(?i)\b(?:b\.?\s*no|per\s*pack)\b", raw):
        return False

    clean = raw.strip(" :;,.-/#*'\t\n\r—&+")
    if len(clean) < 3 or len(clean) > 40:
        return False

    # Reject short all-caps non-word abbreviations (e.g. BUR, FO, MDD)
    if len(clean) <= 3 and clean.isupper():
        return False

    # Reject dates
    if re.search(r"\b\d{1,2}[\/\-\.](?:[a-zA-Z]{3,9}|\d{1,2})[\/\-\.]\d{2,4}\b", clean):
        return False

    lower = clean.lower()

    # Reject obvious flavor / descriptor marketing phrases
    if any(d in lower for d in DESCRIPTOR_OR_FLAVOR_BLACKLIST):
        return False

    # Reject currency / unit price declarations
    if re.search(r"(?:Rs\.?|INR|[₹?])\s*\d+", clean, re.I):
        return False
    if re.search(r"\bper\s+(?:g|kg|ml|l|unit|pack|pc|piece)\b", clean, re.I):
        return False

    # Reject strings without vowels (abbreviations, code blocks, consonant clusters like MDD, BN, etc.)
    if not any(v in lower for v in "aeiouy"):
        return False

    # Reject lines containing nutrient measurement units in parentheses like (g), (mg), (kcal), (%)
    if re.search(r"\(\s*(?:g|mg|kcal|ml|kg|%)\s*\)", raw, re.I) or "%" in raw:
        return False

    # Reject nutritional table keywords
    if any(nutr_kw in lower for nutr_kw in ["sugar", "fat", "protein", "sodium", "cholesterol", "carbohydrate", "energy"]):
        return False

    # Reject run-on instructions or sentence fragments
    if any(len(tok) > 20 for tok in clean.split()):
        return False
    if any(instr_kw in lower for instr_kw in ["onceopened", "refrigerat", "whichever", "earlier", "storage", "direction", "instruction", "dietary"]):
        return False

    # Reject URLs, websites, and emails
    if any(url_indicator in lower for url_indicator in ["www.", ".com", ".coop", ".org", ".net", "http:", "https:", "@", "website:"]):
        return False



    # Reject addresses containing PIN codes or address combinations
    if re.search(r"\b[1-9]\d{5}\b", clean):
        return False
    if any(addr_term in lower for addr_term in ["road", "street", "marg", "plot", "area", "dist", "pin", "floor"]):
        if "," in clean:
            return False

    # Reject purely numeric or mostly numeric strings
    digits_count = sum(ch.isdigit() for ch in clean)
    alpha_count = sum(ch.isalpha() for ch in clean)
    if alpha_count == 0:
        return False
    if digits_count > 0 and (digits_count / len(clean) >= 0.35):
        return False

    # Reject code-like strings:
    # E.g. alphanumeric codes where letters and digits are concatenated (KAF2151, B123, LOT01)
    tokens = clean.split()
    for token in tokens:
        token_stripped = token.strip("(),.-")
        if re.search(r"[a-zA-Z]+\d{2,}|\d{2,}[a-zA-Z]+", token_stripped):
            return False
        if any(c.isdigit() for c in token_stripped) and any(c.isalpha() for c in token_stripped):
            if len(token_stripped) <= 8 and not re.match(r"^\d+(?:st|nd|rd|th)$", token_stripped, re.I):
                return False

    # Reject noise fragments with solitary parentheses/brackets
    if "(" in clean or ")" in clean:
        if len(clean.split()) <= 1:
            return False

    return True


def extract_product_name(ocr_results: List[Dict[str, Any]], full_text: str) -> Optional[Dict[str, Any]]:
    """
    Extract product name based on visual prominence (bounding box height)
    and location heuristics (upper portion of packaging), filtering out
    known declaration lines and code-like identifiers.
    """
    if not ocr_results:
        return None

    candidates = []

    for item in ocr_results:
        # Require OCR confidence >= threshold to avoid low-confidence noise fragments
        if item.get("confidence", 0.0) < DETECTION_CONFIDENCE_THRESHOLD:
            continue

        text = item["text"].strip()
        lower_text = text.lower()

        # Skip lines containing prominent declaration keywords
        if any(kw in lower_text for kw in DECLARATION_KEYWORD_BLACKLIST):
            continue

        # Filter out code-like, numeric, and invalid candidates
        if not _is_valid_product_name(text):
            continue


        # Compute bounding box height as proxy for font size
        bbox = item["bbox"]
        if bbox and len(bbox) == 4:
            y_coords = [pt[1] for pt in bbox]
            height = max(y_coords) - min(y_coords)
            top_y = min(y_coords)
        else:
            height = 10.0
            top_y = 50.0

        candidates.append({
            "text": text,
            "confidence": item["confidence"],
            "bbox": bbox,
            "height": height,
            "top_y": top_y
        })

    if not candidates:
        return None

    # Sort primarily by text height descending (largest font first),
    # secondary by top_y ascending (higher on package preferred)
    candidates.sort(key=lambda c: (-c["height"], c["top_y"]))

    best = candidates[0]
    return create_detection(
        field_name=FIELD_PRODUCT_NAME,
        value=best["text"],
        raw_match=best["text"],
        confidence=best["confidence"],
        bbox=best["bbox"]
    )


# =========================================================================
# 7. Manufacturer / Packer / Importer Extractor
# =========================================================================

MFG_ENTITY_PATTERNS = [
    # Manufactured by / Packed by / Marketed by / Imported by
    re.compile(
        r"(?:Manufactured|Packed|Packer|Marketed|Imported|Distributed)\s*(?:by)?\s*[:\.]?\s*(.+)",
        re.IGNORECASE
    ),
    # Mfg by / Mfd by (explicitly require 'by' to distinguish from 'Mfg Date' or 'Mfg Dt')
    re.compile(
        r"(?:Mfg|Mfd)\.?\s*(?:by)\s*[:\.]?\s*(.+)",
        re.IGNORECASE
    ),
    re.compile(r"\bMfr\.?\s*[:\.]?\s*(.+)", re.IGNORECASE)
]

COMPANY_INDICATOR_PATTERN = re.compile(
    r"(?i)\b(?:Pvt\.?\s*Ltd\.?|Private\s*Limited|Limited|LLP|Corporation|Federation|Co-?operative)\b|\b\w+(?:Ltd|Limited)\b"
)
EXCLUDE_MFG_KEYWORDS = [
    "nutrition", "fat", "energy", "protein", "sugar", "cholesterol", "sodium",
    "serving", "rda", "mfg date", "mfd date", "use by", "best before", "expiry",
    "lic. no", "fssai", "mrp", "usp", "customer care", "consumer care", "toll free", "helpline"
]


def extract_manufacturer(ocr_results: List[Dict[str, Any]], full_text: str) -> Optional[Dict[str, Any]]:
    """Extract Manufacturer, Packer, or Importer entity and address."""
    # Priority 1: Lines with explicit manufacturer keywords (Manufactured by, Marketed by, etc.)
    for idx, item in enumerate(ocr_results):
        line_text = item["text"]
        lower_line = line_text.lower()

        # Disqualify lines that are date declarations
        if "mfg date" in lower_line or "mfd date" in lower_line or "date of" in lower_line:
            continue

        for pattern in MFG_ENTITY_PATTERNS:
            match = pattern.search(line_text)
            if match:
                matched_val = match.group(1).strip()
                matched_bboxes = [item["bbox"]]
                confidences = [item["confidence"]]

                # Check if subsequent line(s) contain address continuation
                if idx + 1 < len(ocr_results):
                    next_item = ocr_results[idx + 1]
                    next_text = next_item["text"].strip()
                    lower_next = next_text.lower()
                    if not any(kw in lower_next for kw in DECLARATION_KEYWORD_BLACKLIST[:10]):
                        if any(term in lower_next for term in ["pvt", "ltd", "plot", "road", "area", "dist", "state", "india", "pin", "floor"]):
                            matched_val += f", {next_text}"
                            matched_bboxes.append(next_item["bbox"])
                            confidences.append(next_item["confidence"])

                union_bbox = compute_bbox_union(matched_bboxes)
                min_confidence = min(confidences)

                if len(matched_val) >= 3:
                    return create_detection(
                        field_name=FIELD_MANUFACTURER,
                        value=matched_val,
                        raw_match=line_text,
                        confidence=min_confidence,
                        bbox=union_bbox
                    )

    # Priority 2: Company indicator lines (Ltd, Pvt Ltd, Limited, LLP, etc.) without explicit prefix
    for idx, item in enumerate(ocr_results):
        line_text = item["text"].strip()
        lower_line = line_text.lower()

        if any(kw in lower_line for kw in EXCLUDE_MFG_KEYWORDS):
            continue

        if COMPANY_INDICATOR_PATTERN.search(line_text):
            matched_val = line_text
            matched_bboxes = [item["bbox"]] if item.get("bbox") else []
            confidences = [item["confidence"]]

            # Look for associated address line (e.g. lines with pincode or city/state/road keywords)
            for other_idx, other_item in enumerate(ocr_results):
                if other_idx == idx:
                    continue
                o_text = other_item["text"].strip()
                o_lower = o_text.lower()
                if any(kw in o_lower for kw in EXCLUDE_MFG_KEYWORDS):
                    continue
                has_pincode = bool(re.search(r"\b[1-9]\d{5}\b", o_text))
                has_addr_word = any(w in o_lower for w in ["road", "street", "marg", "plot", "area", "dist", "gujarat", "maharashtra", "delhi", "karnataka", "tamil nadu", "india"])
                if (has_pincode or has_addr_word) and not COMPANY_INDICATOR_PATTERN.search(o_text):
                    matched_val += f", {o_text}"
                    if other_item.get("bbox"):
                        matched_bboxes.append(other_item["bbox"])
                    confidences.append(other_item["confidence"])
                    break

            union_bbox = compute_bbox_union(matched_bboxes) if matched_bboxes else item.get("bbox")
            min_confidence = min(confidences) if confidences else item["confidence"]

            if len(matched_val) >= 3:
                return create_detection(
                    field_name=FIELD_MANUFACTURER,
                    value=matched_val,
                    raw_match=line_text,
                    confidence=min_confidence,
                    bbox=union_bbox
                )

    return None


# =========================================================================
# 8. Consumer Care Details Extractor
# =========================================================================

PHONE_PATTERN = re.compile(
    r"(?:\b1800[\s\-]?\d{2,4}(?:[\s\-]?\d{2,4}){1,2}\b|\b(?:\+91[\s\-]?)?[6-9]\d{9}\b|\b0\d{2,4}[\s\-]?\d{6,8}\b)"
)
EMAIL_PATTERN = re.compile(
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
)
CONSUMER_CARE_HEADER_KEYWORDS = [
    "customer care", "consumer care", "feedback", "helpline", "toll free",
    "contact us", "care executive", "complaints", "queries", "contact our"
]
CONSUMER_CARE_PATTERNS = [
    re.compile(r"(?:Consumer|Customer)\s*(?:Care|Service|Helpline|Support|Cell)\s*[:\.]?\s*(.+)", re.IGNORECASE),
    re.compile(r"(?:Toll\s*Free|Helpline|Contact\s*Us)\s*[:\.]?\s*(.+)", re.IGNORECASE),
    re.compile(r"(?:For\s*(?:feedback|complaints|queries))\s*[:\.]?\s*(.+)", re.IGNORECASE)
]


def extract_consumer_care(ocr_results: List[Dict[str, Any]], full_text: str) -> Optional[Dict[str, Any]]:
    """Extract Consumer Care contact details prioritizing phone numbers and emails."""
    found_phones = []
    found_emails = []
    header_bboxes = []
    contact_bboxes = []
    confidences = []
    raw_lines = []

    for item in ocr_results:
        text = item["text"].strip()
        lower = text.lower()

        # Check for care context header
        if any(kw in lower for kw in CONSUMER_CARE_HEADER_KEYWORDS):
            if item.get("bbox"):
                header_bboxes.append(item["bbox"])
            raw_lines.append(text)
            confidences.append(item["confidence"])

        # Check for phone
        phone_matches = PHONE_PATTERN.findall(text)
        for pm in phone_matches:
            clean_p = pm.strip()
            if clean_p not in found_phones:
                found_phones.append(clean_p)
                if item.get("bbox"):
                    contact_bboxes.append(item["bbox"])
                confidences.append(item["confidence"])
                if text not in raw_lines:
                    raw_lines.append(text)

        # Check for email
        email_matches = EMAIL_PATTERN.findall(text)
        for em in email_matches:
            clean_e = em.strip()
            if clean_e not in found_emails:
                found_emails.append(clean_e)
                if item.get("bbox"):
                    contact_bboxes.append(item["bbox"])
                confidences.append(item["confidence"])
                if text not in raw_lines:
                    raw_lines.append(text)

    # Prioritize phone + email
    parts = []
    if found_phones:
        parts.append(found_phones[0])
    if found_emails:
        parts.append(found_emails[0])

    if parts:
        care_value = " | ".join(parts)
        all_bboxes = contact_bboxes or header_bboxes
        min_conf = min(confidences) if confidences else 0.85
        return create_detection(
            field_name=FIELD_CONSUMER_CARE,
            value=care_value,
            raw_match=" | ".join(raw_lines) if raw_lines else care_value,
            confidence=min_conf,
            bbox=compute_bbox_union(all_bboxes)
        )

    # Fallback to explicit pattern match if it has contact info (not prose)
    for item in ocr_results:
        text = item["text"].strip()
        for pattern in CONSUMER_CARE_PATTERNS:
            match = pattern.search(text)
            if match:
                candidate = match.group(1).strip()
                # Must contain numbers, symbols, or contact tokens, not single words like "Executiveat"
                if len(candidate.split()) > 1 and any(ch.isdigit() for ch in candidate):
                    return create_detection(
                        field_name=FIELD_CONSUMER_CARE,
                        value=candidate,
                        raw_match=text,
                        confidence=item["confidence"],
                        bbox=item["bbox"]
                    )

    return None


# =========================================================================
# 9. Unit Sale Price (USP) Extractor
# =========================================================================

RECOGNIZED_UNITS_REGEX = re.compile(
    r"^(?:\d+\s*)?(?:g|gm|gms|gram|grams|kg|kgs|kilogram|kilograms|ml|mls|milliliter|millilitre|l|ltr|litre|litres|liter|liters|unit|units|piece|pieces|pc|pcs|item|items|count|capsule|capsules|tablet|tablets|pack|packet|sachet|sachets|m|meter|metre|meters|metres|cm|sq\.?m|sq\.?cm)$",
    re.IGNORECASE
)

USP_PATTERNS = [
    # Unit Sale Price: Rs. 0.20 / g / USP ₹ 1.50 per ml / USP 0.65 / 100g / USP 0.65/9
    re.compile(
        r"(?:Unit\s*Sale\s*Price|USP|Price\s*per|Rate\s*per)\s*[:\.]?\s*(?:Rs\.?|INR|[₹?])?\s*(\d+(?:[.,]\d+)?)(?:\s*[\/-]+)?\s*(per|\/)\s*([a-zA-Z0-9\s.]+)",
        re.IGNORECASE
    ),
    # Standalone price per unit: Rs. 0.33/- PER g / ₹0.20 per g / Rs. 10 / 100g
    re.compile(
        r"(?:Rs\.?|INR|[₹?])\s*(\d+(?:[.,]\d+)?)(?:\s*[\/-]+)?\s*(per|\/)\s*([a-zA-Z0-9\s.]+)",
        re.IGNORECASE
    ),
    # Price per kg ₹120 / Rate per 100g Rs. 10
    re.compile(
        r"(?:Unit\s*Sale\s*Price|USP|Price\s*per|Rate\s*per)\s*([a-zA-Z0-9\s.]+?)\s*[:\.]?\s*(?:Rs\.?|INR|[₹?])\s*(\d+(?:[.,]\d+)?)",
        re.IGNORECASE
    )
]


def _parse_usp_unit(raw_unit_str: str, is_slash: bool = False) -> Optional[str]:
    """Parse and validate USP unit, with very narrow '9' -> 'g' correction only after slash."""
    raw_unit_str = raw_unit_str.strip().strip(".,;/")
    tokens = raw_unit_str.split()
    if not tokens:
        return None

    # Narrow correction: only when '9' is immediately after USP price slash
    if is_slash and tokens[0] == "9":
        return "g"

    # Single token match: e.g. "g", "kg", "ml", "100g", "pcs"
    if RECOGNIZED_UNITS_REGEX.match(tokens[0]):
        return tokens[0]

    # Two-token match: e.g. "100 g", "100 ml", "1 kg"
    if len(tokens) >= 2:
        two_tok = f"{tokens[0]} {tokens[1]}"
        if RECOGNIZED_UNITS_REGEX.match(two_tok):
            return two_tok

    return None


def extract_unit_sale_price(ocr_results: List[Dict[str, Any]], full_text: str) -> Optional[Dict[str, Any]]:
    """Extract Unit Sale Price (USP) declaration, requiring a recognized unit."""
    for item in ocr_results:
        line_text = item["text"]
        for idx, pattern in enumerate(USP_PATTERNS):
            match = pattern.search(line_text)
            if match:
                if idx in (0, 1):
                    price = match.group(1).replace(",", ".")
                    sep = match.group(2)
                    raw_unit = match.group(3)
                    is_slash = (sep == "/")
                else:
                    price = match.group(2).replace(",", ".")
                    raw_unit = match.group(1)
                    is_slash = False

                valid_unit = _parse_usp_unit(raw_unit, is_slash=is_slash)
                if valid_unit:
                    val_str = f"₹{price} / {valid_unit}"
                    return create_detection(
                        field_name=FIELD_UNIT_SALE_PRICE,
                        value=val_str,
                        raw_match=line_text,
                        confidence=item["confidence"],
                        bbox=item["bbox"]
                    )
    return None



# =========================================================================
# Complete Field Extractor Registry (All 9 Mandatory Fields)
# =========================================================================

ALL_EXTRACTORS = [
    (FIELD_PRODUCT_NAME, extract_product_name),
    (FIELD_MANUFACTURER, extract_manufacturer),
    (FIELD_NET_QUANTITY, extract_net_quantity),
    (FIELD_MRP, extract_mrp),
    (FIELD_MFG_DATE, extract_manufacturing_date),
    (FIELD_CONSUMER_CARE, extract_consumer_care),
    (FIELD_COUNTRY_OF_ORIGIN, extract_country_of_origin),
    (FIELD_BEST_BEFORE, extract_best_before),
    (FIELD_UNIT_SALE_PRICE, extract_unit_sale_price),
]

CORE_EXTRACTORS = [
    (FIELD_MRP, extract_mrp),
    (FIELD_NET_QUANTITY, extract_net_quantity),
    (FIELD_COUNTRY_OF_ORIGIN, extract_country_of_origin),
    (FIELD_MFG_DATE, extract_manufacturing_date),
    (FIELD_BEST_BEFORE, extract_best_before),
]


def extract_core_fields(ocr_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run the first 5 core extractors against OCR results."""
    full_text = "\n".join(item["text"] for item in ocr_results)
    detections: List[Dict[str, Any]] = []

    for field_name, extractor_fn in CORE_EXTRACTORS:
        det = extractor_fn(ocr_results, full_text)
        if det:
            detections.append(det)
        else:
            detections.append(create_empty_detection(field_name))

    return detections


def extract_all_fields(ocr_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run all 9 mandatory field extractors against OCR results.
    Returns a standardized list of 9 detection dictionaries.
    """
    full_text = "\n".join(item["text"] for item in ocr_results)
    detections: List[Dict[str, Any]] = []

    for field_name, extractor_fn in ALL_EXTRACTORS:
        det = extractor_fn(ocr_results, full_text)
        if det:
            detections.append(det)
        else:
            detections.append(create_empty_detection(field_name))

    return detections


def _normalize_value_for_comparison(field: str, value: Optional[str]) -> Any:
    """Helper to normalize values for cross-image conflict comparison."""
    if value is None:
        return ""
    val = str(value).strip().lower()
    if field in (FIELD_MRP, FIELD_UNIT_SALE_PRICE):
        try:
            return float(val)
        except ValueError:
            pass
    return val


def merge_detections(
    per_image_detections: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Merge field detections from multiple image views into a single
    list of 9 detections, one per mandatory field.

    Args:
        per_image_detections: Dict mapping image role to its detections list.
            Example: {"front": [...9 detections...], "back": [...9 detections...]}

    Returns:
        List of 9 merged detection dicts, one per mandatory field.
        Each detection has source_image set.
        Ambiguous fields have status="ambiguous" and a "candidates" list.
    """
    merged: List[Dict[str, Any]] = []

    for field_name in MANDATORY_FIELDS:
        field_candidates: List[Dict[str, Any]] = []

        for role, dets in per_image_detections.items():
            if not dets:
                continue
            for det in dets:
                if det.get("field") == field_name:
                    if det.get("status") in (STATUS_FOUND, STATUS_LOW_CONFIDENCE):
                        det_copy = dict(det)
                        if not det_copy.get("source_image"):
                            det_copy["source_image"] = role
                        field_candidates.append(det_copy)

        if len(field_candidates) == 0:
            merged.append(create_empty_detection(field_name))
        elif len(field_candidates) == 1:
            merged.append(dict(field_candidates[0]))
        else:
            # Sort by confidence descending
            field_candidates.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
            norm_vals = [_normalize_value_for_comparison(field_name, c.get("value")) for c in field_candidates]
            all_equal = all(v == norm_vals[0] for v in norm_vals)

            primary = dict(field_candidates[0])
            if all_equal:
                primary["status"] = STATUS_FOUND
            else:
                primary["status"] = STATUS_AMBIGUOUS
                primary["candidates"] = [
                    {
                        "value": c.get("value"),
                        "confidence": c.get("confidence"),
                        "source_image": c.get("source_image"),
                        "bbox": c.get("bbox")
                    }
                    for c in field_candidates
                ]
            merged.append(primary)

    return merged

