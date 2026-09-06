"""
Tests for Field Extraction Module (extractor.py)
Tests regex patterns, heuristics, normalization, and bounding box computation.
"""

import pytest
from extractor import (
    extract_mrp,
    extract_net_quantity,
    extract_country_of_origin,
    extract_manufacturing_date,
    extract_best_before,
    extract_product_name,
    extract_manufacturer,
    extract_consumer_care,
    extract_unit_sale_price,
    extract_core_fields,
    extract_all_fields,
    compute_bbox_union,
    merge_detections
)
from config import (
    FIELD_MRP,
    FIELD_NET_QUANTITY,
    FIELD_COUNTRY_OF_ORIGIN,
    FIELD_MFG_DATE,
    FIELD_BEST_BEFORE,
    FIELD_PRODUCT_NAME,
    FIELD_MANUFACTURER,
    FIELD_CONSUMER_CARE,
    FIELD_UNIT_SALE_PRICE,
    MANDATORY_FIELDS
)
from schemas import STATUS_FOUND, STATUS_NOT_FOUND, STATUS_AMBIGUOUS, create_detection, create_empty_detection



def make_ocr_item(text: str, confidence: float = 0.95, bbox=None):
    if bbox is None:
        bbox = [[0.0, 10.0], [100.0, 10.0], [100.0, 30.0], [0.0, 30.0]]
    return {"text": text, "confidence": confidence, "bbox": bbox}


# --------------------------------------------------------------------------
# 1. MRP Extraction Tests
# --------------------------------------------------------------------------

def test_extract_mrp_rupee_symbol():
    items = [make_ocr_item("MRP ₹120.00 (incl. of all taxes)")]
    res = extract_mrp(items, items[0]["text"])
    assert res is not None
    assert res["field"] == FIELD_MRP
    assert res["value"] == "120.00"
    assert res["status"] == STATUS_FOUND


def test_extract_mrp_rs_prefix():
    items = [make_ocr_item("M.R.P. Rs. 45.50")]
    res = extract_mrp(items, items[0]["text"])
    assert res is not None
    assert res["value"] == "45.50"


def test_extract_mrp_integer():
    items = [make_ocr_item("MRP: Rs 250")]
    res = extract_mrp(items, items[0]["text"])
    assert res is not None
    assert res["value"] == "250"


def test_extract_mrp_not_found():
    items = [make_ocr_item("Random product ingredients and nutrition facts")]
    res = extract_mrp(items, items[0]["text"])
    assert res is None


# --------------------------------------------------------------------------
# 2. Net Quantity Extraction Tests
# --------------------------------------------------------------------------

def test_extract_net_qty_grams():
    items = [make_ocr_item("Net Wt.: 100g")]
    res = extract_net_quantity(items, items[0]["text"])
    assert res is not None
    assert res["field"] == FIELD_NET_QUANTITY
    assert res["value"] == "100 g"
    assert res["status"] == STATUS_FOUND


def test_extract_net_qty_unit_normalization():
    items = [make_ocr_item("Net Quantity: 500 gms")]
    res = extract_net_quantity(items, items[0]["text"])
    assert res is not None
    assert res["value"] == "500 g"


def test_extract_net_qty_liters():
    items = [make_ocr_item("Net Content: 1.5 L")]
    res = extract_net_quantity(items, items[0]["text"])
    assert res is not None
    assert res["value"] == "1.5 l"


def test_extract_net_qty_ml():
    items = [make_ocr_item("Net Volume: 750 mL")]
    res = extract_net_quantity(items, items[0]["text"])
    assert res is not None
    assert res["value"] == "750 ml"


# --------------------------------------------------------------------------
# 3. Country of Origin Tests
# --------------------------------------------------------------------------

def test_extract_country_of_origin_explicit():
    items = [make_ocr_item("Country of Origin: India")]
    res = extract_country_of_origin(items, items[0]["text"])
    assert res is not None
    assert res["field"] == FIELD_COUNTRY_OF_ORIGIN
    assert res["value"] == "India"
    assert res["status"] == STATUS_FOUND


def test_extract_country_of_origin_made_in():
    items = [make_ocr_item("Made in Germany, packaged in EU")]
    res = extract_country_of_origin(items, items[0]["text"])
    assert res is not None
    assert res["value"] == "Germany"


def test_extract_country_of_origin_typo_correction():
    # Common OCR misreading 'lndia' instead of 'India'
    items = [make_ocr_item("Country of Origin: lndia")]
    res = extract_country_of_origin(items, items[0]["text"])
    assert res is not None
    assert res["value"] == "India"


# --------------------------------------------------------------------------
# 4. Manufacturing Date Tests
# --------------------------------------------------------------------------

def test_extract_mfg_date_standard():
    items = [make_ocr_item("Mfg. Date: 03/2026")]
    res = extract_manufacturing_date(items, items[0]["text"])
    assert res is not None
    assert res["field"] == FIELD_MFG_DATE
    assert res["value"] == "03/2026"
    assert res["status"] == STATUS_FOUND


def test_extract_mfg_date_month_name():
    items = [make_ocr_item("Packed on: Mar 2026")]
    res = extract_manufacturing_date(items, items[0]["text"])
    assert res is not None
    assert "Mar 2026" in res["value"]


# --------------------------------------------------------------------------
# 5. Best Before / Expiry Tests
# --------------------------------------------------------------------------

def test_extract_best_before_duration():
    items = [make_ocr_item("Best Before 12 months from Mfg")]
    res = extract_best_before(items, items[0]["text"])
    assert res is not None
    assert res["field"] == FIELD_BEST_BEFORE
    assert "12 months" in res["value"]
    assert res["status"] == STATUS_FOUND


def test_extract_use_by_date():
    items = [make_ocr_item("Use By: 31/12/2026")]
    res = extract_best_before(items, items[0]["text"])
    assert res is not None
    assert "31/12/2026" in res["value"]


# --------------------------------------------------------------------------
# 6. Core Extractors Integration & BBox Union Tests
# --------------------------------------------------------------------------

def test_extract_core_fields_full():
    items = [
        make_ocr_item("Parle-G Gold Biscuits"),
        make_ocr_item("Net Wt: 100g"),
        make_ocr_item("MRP Rs. 20.00 (incl. of all taxes)"),
        make_ocr_item("Mfg Date: 03/2026"),
        make_ocr_item("Best Before: 6 months"),
        make_ocr_item("Country of Origin: India")
    ]
    detections = extract_core_fields(items)
    assert len(detections) == 5

    field_map = {d["field"]: d for d in detections}
    assert field_map[FIELD_MRP]["status"] == STATUS_FOUND
    assert field_map[FIELD_MRP]["value"] == "20.00"
    assert field_map[FIELD_NET_QUANTITY]["status"] == STATUS_FOUND
    assert field_map[FIELD_COUNTRY_OF_ORIGIN]["status"] == STATUS_FOUND
    assert field_map[FIELD_MFG_DATE]["status"] == STATUS_FOUND
    assert field_map[FIELD_BEST_BEFORE]["status"] == STATUS_FOUND


def test_compute_bbox_union():
    bbox1 = [[10.0, 20.0], [50.0, 20.0], [50.0, 40.0], [10.0, 40.0]]
    bbox2 = [[15.0, 45.0], [80.0, 45.0], [80.0, 65.0], [15.0, 65.0]]

    union = compute_bbox_union([bbox1, bbox2])
    assert union is not None
    # min_x=10, min_y=20, max_x=80, max_y=65
    assert union == [
        [10.0, 20.0],
        [80.0, 20.0],
        [80.0, 65.0],
        [10.0, 65.0]
    ]


# --------------------------------------------------------------------------
# 7. Additional 4 Field Extractors & Full Extraction
# --------------------------------------------------------------------------

def test_extract_product_name_prominence():
    items = [
        # Prominent title text (height = 50px)
        make_ocr_item("Britannia Good Day Butter", bbox=[[10.0, 20.0], [200.0, 20.0], [200.0, 70.0], [10.0, 70.0]]),
        # Smaller declaration lines
        make_ocr_item("Net Wt: 200g", bbox=[[10.0, 80.0], [100.0, 80.0], [100.0, 100.0], [10.0, 100.0]]),
        make_ocr_item("MRP Rs. 35.00", bbox=[[10.0, 110.0], [100.0, 110.0], [100.0, 130.0], [10.0, 130.0]])
    ]
    res = extract_product_name(items, "")
    assert res is not None
    assert res["field"] == FIELD_PRODUCT_NAME
    assert res["value"] == "Britannia Good Day Butter"
    assert res["status"] == STATUS_FOUND


def test_extract_manufacturer_standard():
    items = [
        make_ocr_item("Manufactured by: Parle Products Pvt. Ltd."),
        make_ocr_item("North Level Crossing, Vile Parle East, Mumbai 400057")
    ]
    res = extract_manufacturer(items, "")
    assert res is not None
    assert res["field"] == FIELD_MANUFACTURER
    assert "Parle Products" in res["value"]
    assert res["status"] == STATUS_FOUND


def test_extract_consumer_care_helpline():
    items = [
        make_ocr_item("Customer Care: 1800-22-2211"),
        make_ocr_item("Email: customercare@parle.biz")
    ]
    res = extract_consumer_care(items, "")
    assert res is not None
    assert res["field"] == FIELD_CONSUMER_CARE
    assert "1800-22-2211" in res["value"]
    assert res["status"] == STATUS_FOUND


def test_extract_unit_sale_price_standard():
    items = [make_ocr_item("Unit Sale Price: Rs. 0.20 / g")]
    res = extract_unit_sale_price(items, "")
    assert res is not None
    assert res["field"] == FIELD_UNIT_SALE_PRICE
    assert "0.20" in res["value"]
    assert res["status"] == STATUS_FOUND


def test_extract_all_fields_returns_nine():
    items = [
        make_ocr_item("Britannia Milk Bikis", bbox=[[10.0, 10.0], [200.0, 10.0], [200.0, 60.0], [10.0, 60.0]]),
        make_ocr_item("Net Wt: 150g"),
        make_ocr_item("MRP ₹30.00"),
        make_ocr_item("Mfg Date: 01/2026"),
        make_ocr_item("Best Before: 9 months"),
        make_ocr_item("Country of Origin: India"),
        make_ocr_item("Manufactured by: Britannia Industries Ltd."),
        make_ocr_item("Consumer Care: 1800-425-4449"),
        make_ocr_item("Unit Sale Price: ₹0.20 per g")
    ]
    detections = extract_all_fields(items)
    assert len(detections) == 9

    field_map = {d["field"]: d for d in detections}
    for field in [
        FIELD_PRODUCT_NAME, FIELD_MANUFACTURER, FIELD_NET_QUANTITY,
        FIELD_MRP, FIELD_MFG_DATE, FIELD_CONSUMER_CARE,
        FIELD_COUNTRY_OF_ORIGIN, FIELD_BEST_BEFORE, FIELD_UNIT_SALE_PRICE
    ]:
        assert field in field_map
        assert field_map[field]["status"] == STATUS_FOUND


# --------------------------------------------------------------------------
# 8. Merge Detections Tests (Multi-Image)
# --------------------------------------------------------------------------

def test_merge_single_image():
    """Single image detections pass through unchanged."""
    items = [make_ocr_item("MRP Rs. 20.00")]
    dets = extract_all_fields(items)
    merged = merge_detections({"front": dets})
    assert len(merged) == 9
    mrp = [d for d in merged if d["field"] == FIELD_MRP][0]
    assert mrp["status"] == STATUS_FOUND
    assert mrp["value"] == "20.00"
    assert mrp["source_image"] == "front"


def test_merge_consistent_values():
    """Same field on front and back with same value -> highest confidence wins."""
    front_dets = [create_detection(FIELD_MRP, "20.00", "MRP Rs. 20.00", 0.90, [[0, 0], [10, 0], [10, 10], [0, 10]], source_image="front")] + [create_empty_detection(f) for f in MANDATORY_FIELDS if f != FIELD_MRP]
    back_dets = [create_detection(FIELD_MRP, "20.00", "MRP Rs. 20.00", 0.95, [[0, 0], [20, 0], [20, 10], [0, 10]], source_image="back")] + [create_empty_detection(f) for f in MANDATORY_FIELDS if f != FIELD_MRP]
    merged = merge_detections({"front": front_dets, "back": back_dets})
    mrp = [d for d in merged if d["field"] == FIELD_MRP][0]
    assert mrp["status"] == STATUS_FOUND
    assert mrp["confidence"] == 0.95
    assert mrp["source_image"] == "back"


def test_merge_conflicting_values():
    """Different MRP values -> status is ambiguous with candidates."""
    front_dets = [create_detection(FIELD_MRP, "120.00", "MRP Rs. 120.00", 0.94, [[0, 0], [10, 0], [10, 10], [0, 10]], source_image="front")] + [create_empty_detection(f) for f in MANDATORY_FIELDS if f != FIELD_MRP]
    back_dets = [create_detection(FIELD_MRP, "110.00", "MRP Rs. 110.00", 0.91, [[0, 0], [20, 0], [20, 10], [0, 10]], source_image="back")] + [create_empty_detection(f) for f in MANDATORY_FIELDS if f != FIELD_MRP]
    merged = merge_detections({"front": front_dets, "back": back_dets})
    mrp = [d for d in merged if d["field"] == FIELD_MRP][0]
    assert mrp["status"] == STATUS_AMBIGUOUS
    assert "candidates" in mrp
    assert len(mrp["candidates"]) == 2
    assert mrp["value"] == "120.00"
    assert mrp["candidates"][0]["value"] == "120.00"
    assert mrp["candidates"][1]["value"] == "110.00"


def test_merge_field_only_on_back():
    """Field found only on back image -> source_image is 'back'."""
    front_dets = [create_empty_detection(f) for f in MANDATORY_FIELDS]
    back_dets = [create_detection(FIELD_MRP, "20.00", "MRP Rs. 20.00", 0.95, [[0, 0], [20, 0], [20, 10], [0, 10]], source_image="back")] + [create_empty_detection(f) for f in MANDATORY_FIELDS if f != FIELD_MRP]
    merged = merge_detections({"front": front_dets, "back": back_dets})
    mrp = [d for d in merged if d["field"] == FIELD_MRP][0]
    assert mrp["source_image"] == "back"
    assert mrp["status"] == STATUS_FOUND


def test_merge_with_side_image():
    """Three images merge correctly."""
    f_dets = [create_detection(FIELD_PRODUCT_NAME, "Parle-G", "Parle-G", 0.98, None, source_image="front")] + [create_empty_detection(f) for f in MANDATORY_FIELDS if f != FIELD_PRODUCT_NAME]
    b_dets = [create_detection(FIELD_MRP, "20.00", "MRP Rs. 20.00", 0.95, None, source_image="back")] + [create_empty_detection(f) for f in MANDATORY_FIELDS if f != FIELD_MRP]
    s_dets = [create_detection(FIELD_CONSUMER_CARE, "1800-22-2211", "1800-22-2211", 0.92, None, source_image="side")] + [create_empty_detection(f) for f in MANDATORY_FIELDS if f != FIELD_CONSUMER_CARE]
    merged = merge_detections({"front": f_dets, "back": b_dets, "side": s_dets})
    assert len(merged) == 9
    field_map = {d["field"]: d for d in merged}
    assert field_map[FIELD_PRODUCT_NAME]["status"] == STATUS_FOUND
    assert field_map[FIELD_PRODUCT_NAME]["source_image"] == "front"
    assert field_map[FIELD_MRP]["status"] == STATUS_FOUND
    assert field_map[FIELD_MRP]["source_image"] == "back"
    assert field_map[FIELD_CONSUMER_CARE]["status"] == STATUS_FOUND
    assert field_map[FIELD_CONSUMER_CARE]["source_image"] == "side"
    assert field_map[FIELD_NET_QUANTITY]["status"] == STATUS_NOT_FOUND


# --------------------------------------------------------------------------
# 9. Real Product Edge Case Regression Tests (Amul inspection fixes)
# --------------------------------------------------------------------------

def test_product_name_rejects_code_identifiers():
    """Verify code-like identifiers (:KAF2151, 7116, B123) are rejected as product names."""
    # When back label only contains codes and instructions, product name must be None
    code_items = [
        make_ocr_item(":KAF2151", bbox=[[10.0, 10.0], [200.0, 10.0], [200.0, 60.0], [10.0, 60.0]]),
        make_ocr_item("7116", bbox=[[10.0, 70.0], [100.0, 70.0], [100.0, 110.0], [10.0, 110.0]]),
        make_ocr_item("EXPIRY DATE,WHICHEVERIS EARLIER.", bbox=[[10.0, 120.0], [300.0, 120.0], [300.0, 150.0], [10.0, 150.0]]),
    ]
    assert extract_product_name(code_items, "") is None

    # When mixed with real brand name, real name wins and code is rejected
    mixed_items = [
        make_ocr_item(":KAF2151", bbox=[[10.0, 10.0], [200.0, 10.0], [200.0, 60.0], [10.0, 60.0]]),
        make_ocr_item("Amul", bbox=[[10.0, 70.0], [200.0, 70.0], [200.0, 120.0], [10.0, 120.0]])
    ]
    res = extract_product_name(mixed_items, "")
    assert res is not None
    assert res["value"] == "Amul"
    assert res["status"] == STATUS_FOUND


def test_consumer_care_extracts_phone_and_email_not_prose():
    """Extract actual contact info (phone + email), never returning just 'Executiveat'."""
    items = [
        make_ocr_item("We appreciate your feedback. Contact our Customer Care Executiveat"),
        make_ocr_item("Cholesterol (mg)"),
        make_ocr_item("1800 2583333 (Toll free) [6 AM-9 PM]"),
        make_ocr_item("0.0"),
        make_ocr_item("customercare@amul.coop")
    ]
    res = extract_consumer_care(items, "")
    assert res is not None
    assert res["field"] == FIELD_CONSUMER_CARE
    assert "1800 2583333" in res["value"]
    assert "customercare@amul.coop" in res["value"]
    assert "Executiveat" not in res["value"]
    assert res["status"] == STATUS_FOUND


def test_best_before_rejects_prose_expiry_disclaimer():
    """Reject prose 'EXPIRY DATE,WHICHEVERIS EARLIER.' without date/duration."""
    # Invalid prose disclaimer
    item_prose = [make_ocr_item("EXPIRY DATE,WHICHEVERIS EARLIER.")]
    assert extract_best_before(item_prose, "") is None

    # Valid duration
    res1 = extract_best_before([make_ocr_item("Best Before 12 months")], "")
    assert res1 is not None
    assert "12 months" in res1["value"]
    assert res1["status"] == STATUS_FOUND

    # Valid date
    res2 = extract_best_before([make_ocr_item("Use By 31/12/2026")], "")
    assert res2 is not None
    assert "31/12/2026" in res2["value"]

    # Valid shelf life
    res3 = extract_best_before([make_ocr_item("Shelf Life 6 months")], "")
    assert res3 is not None
    assert "6 months" in res3["value"]


def test_unit_sale_price_requires_recognized_unit():
    """Verify recognized unit contexts and narrow /9 correction only in USP slash context."""
    # Narrow correction: 'USP 0.65/9' is accepted in USP slash context as 'g'
    res_usp_9 = extract_unit_sale_price([make_ocr_item("USP 0.65/9")], "")
    assert res_usp_9 is not None
    assert res_usp_9["value"] == "₹0.65 / g"
    assert res_usp_9["status"] == STATUS_FOUND

    # Standalone '9' without slash or non-USP context is not accepted
    assert extract_unit_sale_price([make_ocr_item("Price per 9 ₹120")], "") is None
    assert extract_unit_sale_price([make_ocr_item("USP 0.65 per 9")], "") is None
    assert extract_unit_sale_price([make_ocr_item("USP 0.65 / 10")], "") is None

    # Valid: 'per 100g'
    res1 = extract_unit_sale_price([make_ocr_item("Unit Sale Price: ₹10 per 100g")], "")
    assert res1 is not None
    assert "10" in res1["value"]
    assert "100g" in res1["value"]
    assert res1["status"] == STATUS_FOUND

    # Valid: 'per kg'
    res2 = extract_unit_sale_price([make_ocr_item("Price per kg ₹120")], "")
    assert res2 is not None
    assert "120" in res2["value"]
    assert "kg" in res2["value"]

    # Valid: 'USP ₹0.20 per g'
    res3 = extract_unit_sale_price([make_ocr_item("USP ₹0.20 per g")], "")
    assert res3 is not None
    assert "0.20" in res3["value"]
    assert "g" in res3["value"]


def test_manufacturer_extracts_company_and_address_without_keyword():
    """Extract company and address when 'Manufactured by' prefix is absent."""
    items = [
        make_ocr_item("Nutritional Information"),
        make_ocr_item("Anand,Gujarat-388001,India.Website:www.amul.com"),
        make_ocr_item("Total Fat (g)"),
        make_ocr_item("GCMMFLtd.,Anand-388001")
    ]
    res = extract_manufacturer(items, "")
    assert res is not None
    assert res["field"] == FIELD_MANUFACTURER
    assert "GCMMF" in res["value"]
    assert "Anand" in res["value"]
    assert res["status"] == STATUS_FOUND

    # Verify Country of Origin is NOT inferred merely by 'India' inside manufacturer address
    coo = extract_country_of_origin(items, "")
    assert coo is None


def test_product_name_rejects_pkd_declaration_and_accepts_amul():
    """Reject declaration/code patterns like 'PKD:03/AUG/26' and accept real product names like 'Amul'."""
    # PKD alone is rejected
    assert extract_product_name([make_ocr_item("PKD:03/AUG/26")], "") is None
    assert extract_product_name([make_ocr_item("EXP:03/AUG/27")], "") is None
    assert extract_product_name([make_ocr_item("BN:KAF2151")], "") is None
    assert extract_product_name([make_ocr_item("MFD:03/AUG/26")], "") is None
    assert extract_product_name([make_ocr_item("USP:0.65/g")], "") is None
    assert extract_product_name([make_ocr_item("MDD")], "") is None

    # Mixed list with 'Amul' and 'PKD:03/AUG/26'
    items = [
        make_ocr_item("PKD:03/AUG/26", bbox=[[10.0, 10.0], [200.0, 10.0], [200.0, 60.0], [10.0, 60.0]]),
        make_ocr_item("Amul", bbox=[[10.0, 70.0], [200.0, 70.0], [200.0, 120.0], [10.0, 120.0]])
    ]
    res = extract_product_name(items, "")
    assert res is not None
    assert res["value"] == "Amul"
    assert res["status"] == STATUS_FOUND


def test_manufacturing_date_extracts_pkd_and_mfd():
    """Extract manufacturing date from PKD:<date>, PKD: <date>, MFD:<date>, MFD: <date>."""
    res_pkd_nospace = extract_manufacturing_date([make_ocr_item("PKD:03/AUG/26")], "")
    assert res_pkd_nospace is not None
    assert res_pkd_nospace["field"] == FIELD_MFG_DATE
    assert res_pkd_nospace["value"] == "03/AUG/26"
    assert res_pkd_nospace["status"] == STATUS_FOUND

    res_pkd_space = extract_manufacturing_date([make_ocr_item("PKD: 03/AUG/26")], "")
    assert res_pkd_space is not None
    assert res_pkd_space["value"] == "03/AUG/26"

    res_mfd_nospace = extract_manufacturing_date([make_ocr_item("MFD:03/AUG/26")], "")
    assert res_mfd_nospace is not None
    assert res_mfd_nospace["value"] == "03/AUG/26"

    res_mfd_space = extract_manufacturing_date([make_ocr_item("MFD: 03/AUG/26")], "")
    assert res_mfd_space is not None
    assert res_mfd_space["value"] == "03/AUG/26"


def test_best_before_extracts_exp_date():
    """Extract best before date from EXP:<date>, Exp:<date>, Expiry:<date> and reject disclaimer."""
    # From the combined line on real packaging:
    res_combined = extract_best_before([make_ocr_item("T30 USP 0.65/9 EXP:03/AUG/27")], "")
    assert res_combined is not None
    assert res_combined["field"] == FIELD_BEST_BEFORE
    assert res_combined["value"] == "03/AUG/27"
    assert res_combined["status"] == STATUS_FOUND

    # Standalone EXP:
    res_exp = extract_best_before([make_ocr_item("EXP:03/AUG/27")], "")
    assert res_exp is not None
    assert res_exp["value"] == "03/AUG/27"

    # EXP with space:
    res_exp_space = extract_best_before([make_ocr_item("EXP: 03/AUG/27")], "")
    assert res_exp_space is not None
    assert res_exp_space["value"] == "03/AUG/27"

    # Exp:
    res_exp_case = extract_best_before([make_ocr_item("Exp:03/AUG/27")], "")
    assert res_exp_case is not None
    assert res_exp_case["value"] == "03/AUG/27"

    # Expiry:
    res_expiry = extract_best_before([make_ocr_item("Expiry:03/AUG/27")], "")
    assert res_expiry is not None
    assert res_expiry["value"] == "03/AUG/27"

    # Generic disclaimer is still rejected:
    assert extract_best_before([make_ocr_item("EXPIRY DATE,WHICHEVERIS EARLIER.")], "") is None


def test_mrp_remains_not_found_when_no_mrp_number():
    """MRP must return None (not_found) when only disclaimer text is present without a price number."""
    item = make_ocr_item("For MRP (incl. ofall taxes), Date of Packaging (Pkd.) & Expiry (Exp.), Batch No. (BN), see below.")
    assert extract_mrp([item], item["text"]) is None


def test_product_name_rejects_flavors_and_descriptors():
    """Reject obvious flavors and descriptor phrases like 'MAGIC MASALA', 'INDIA'S', 'FINEST POTATOES'."""
    assert extract_product_name([make_ocr_item("MAGIC MASALA")], "") is None
    assert extract_product_name([make_ocr_item("INDIA'S")], "") is None
    assert extract_product_name([make_ocr_item("FINEST POTATOES")], "") is None
    assert extract_product_name([make_ocr_item("MADEWITH")], "") is None
    assert extract_product_name([make_ocr_item("MADE WITH")], "") is None

    # Full Lay's front OCR sample items where brand Lay's was missed by OCR
    lays_front_items = [
        make_ocr_item("—COLOU"),
        make_ocr_item("&FLAV"),
        make_ocr_item("S"),
        make_ocr_item("ay"),
        make_ocr_item("TM"),
        make_ocr_item("INDIA'S"),
        make_ocr_item("MAGIC MASALA"),
        make_ocr_item("MADEWITH"),
        make_ocr_item("FINEST POTATOES")
    ]
    # Must return None rather than fabricating Lay's or returning MAGIC MASALA
    assert extract_product_name(lays_front_items, "") is None

    # Real brands are still accepted
    assert extract_product_name([make_ocr_item("Amul")], "")["value"] == "Amul"
    assert extract_product_name([make_ocr_item("Good Day")], "")["value"] == "Good Day"
    assert extract_product_name([make_ocr_item("Parle-G Gold Biscuits")], "")["value"] == "Parle-G Gold Biscuits"


def test_manufacturing_date_joint_mfd_use_by():
    """Extract date1 from joint 'MFD & USE BY: date1 & date2' declarations."""
    # On same line
    res1 = extract_manufacturing_date([make_ocr_item("MFD & USE BY: 25/08/26 & 07/01/27")], "")
    assert res1 is not None
    assert res1["value"] == "25/08/26"
    assert res1["status"] == STATUS_FOUND

    # On separate lines (like Lay's real sample)
    items = [
        make_ocr_item("25/08/26 & 07/01/27"),
        make_ocr_item("MFD & USE BY:")
    ]
    res2 = extract_manufacturing_date(items, "")
    assert res2 is not None
    assert res2["value"] == "25/08/26"
    assert res2["status"] == STATUS_FOUND


def test_best_before_joint_mfd_use_by():
    """Extract date2 from joint 'MFD & USE BY: date1 & date2' declarations."""
    # On same line
    res1 = extract_best_before([make_ocr_item("MFD & USE BY: 25/08/26 & 07/01/27")], "")
    assert res1 is not None
    assert res1["value"] == "07/01/27"
    assert res1["status"] == STATUS_FOUND

    # On separate lines (like Lay's real sample)
    items = [
        make_ocr_item("25/08/26 & 07/01/27"),
        make_ocr_item("MFD & USE BY:")
    ]
    res2 = extract_best_before(items, "")
    assert res2 is not None
    assert res2["value"] == "07/01/27"
    assert res2["status"] == STATUS_FOUND


def test_unit_sale_price_slash_dash_per_g():
    """Support valid format 'Rs. 0.33/- PER g' and maintain strict unit requirements."""
    res1 = extract_unit_sale_price([make_ocr_item("Rs. 0.33/- PER g")], "")
    assert res1 is not None
    assert res1["value"] == "₹0.33 / g"
    assert res1["status"] == STATUS_FOUND

    res2 = extract_unit_sale_price([make_ocr_item("Rs. 0.33 / g")], "")
    assert res2 is not None
    assert res2["value"] == "₹0.33 / g"

    # Arbitrary text rejected
    assert extract_unit_sale_price([make_ocr_item("0.65/9")], "") is None
    assert extract_unit_sale_price([make_ocr_item("Rs. 10 per randomunit")], "") is None


def test_net_quantity_promotional_and_nutrition_rejection():
    """Support standalone '30.5 g (28 g+2.5 g)' and reject nutrition values."""
    res1 = extract_net_quantity([make_ocr_item("30.5 g (28 g+2.5 g)")], "")
    assert res1 is not None
    assert res1["value"] == "30.5 g"
    assert res1["status"] == STATUS_FOUND

    res2 = extract_net_quantity([make_ocr_item("30.5g (28g+2.5g)")], "")
    assert res2 is not None
    assert res2["value"] == "30.5 g"

    # Avoid extracting standalone nutrition table numbers as net quantity
    nutrition_items = [
        make_ocr_item("6.6g"),
        make_ocr_item("0.9g"),
        make_ocr_item("14.9 g"),
        make_ocr_item("33 g"),
        make_ocr_item("51.9g")
    ]
    assert extract_net_quantity(nutrition_items, "") is None


def test_manufacturer_not_found_when_only_fragment():
    """Do not fabricate manufacturer when OCR only captures fragment like 'Mfg. & Mk'."""
    items = [make_ocr_item("Mfg. & Mk")]
    assert extract_manufacturer(items, "") is None




