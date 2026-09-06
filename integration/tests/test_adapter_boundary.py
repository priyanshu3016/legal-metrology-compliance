"""
Adapter boundary tests: Verify conversion from Person 5 AI result structures
to Person 6 StructuredFacts and subsequent compliance checks evaluation without running OCR.
"""

from backend.compliance.adapter import ai_result_to_structured_facts
from backend.compliance.engine import run_compliance_checks
from backend.compliance.schemas import StructuredFacts, ComplianceResult

LAYS_AI_RESULT = {
    "success": True,
    "image_paths": {
        "front": "samples/1.jpg",
        "back": "samples/2.jpg",
        "side": None,
    },
    "image_path": "samples/1.jpg",
    "image_id": "1",
    "timestamp": "2026-09-05T16:26:06.123456+00:00",
    "processing_time_ms": 1420,
    "raw_ocr": {
        "front": {
            "full_text": "—COLOU\n&FLAV\nS\nay\nTM\nINDIA'S\nMAGIC MASALA\nMADEWITH\nFINEST POTATOES",
            "line_count": 9,
            "avg_confidence": 0.9904,
        },
        "back": {
            "full_text": "OR CALL US AT 1800 22 4020\nCONSUMER.FEEDBACK@PEPSICO.COM\nMRP Rs. 10/- (INCL. OF ALL TAXES)\nUNIT SALE PRICE:\nRs. 0.33/- PER g\n25/08/26 & 07/01/27\nMFD & USE BY:\n30.5 g (28 g+2.5 g)",
            "line_count": 32,
            "avg_confidence": 0.9621,
        },
        "side": None,
    },
    "detections": [
        {
            "field": "product_name",
            "label": "Product Name",
            "value": None,
            "raw_match": None,
            "confidence": 0.0,
            "bbox": None,
            "source": "ocr",
            "source_image": None,
            "status": "not_found",
        },
        {
            "field": "manufacturer_packer_importer",
            "label": "Manufacturer / Packer / Importer",
            "value": None,
            "raw_match": None,
            "confidence": 0.0,
            "bbox": None,
            "source": "ocr",
            "source_image": None,
            "status": "not_found",
        },
        {
            "field": "net_quantity",
            "label": "Net Quantity",
            "value": "30.5 g",
            "raw_match": "30.5 g (28 g+2.5 g)",
            "confidence": 0.8978,
            "bbox": [[866.0, 3426.0], [1225.0, 3431.0], [1223.0, 3549.0], [865.0, 3544.0]],
            "source": "ocr",
            "source_image": "back",
            "status": "found",
        },
        {
            "field": "mrp",
            "label": "Maximum Retail Price",
            "value": "10",
            "raw_match": "MRP Rs. 10/- (INCL. OF ALL TAXES)",
            "confidence": 0.9978,
            "bbox": [[87.0, 2868.0], [1359.0, 2796.0], [1365.0, 2898.0], [93.0, 2970.0]],
            "source": "ocr",
            "source_image": "back",
            "status": "found",
        },
        {
            "field": "manufacturing_date",
            "label": "Manufacturing / Packing Date",
            "value": "25/08/26",
            "raw_match": "25/08/26 & 07/01/27",
            "confidence": 0.998,
            "bbox": [[866.0, 3323.0], [1358.0, 3321.0], [1359.0, 3400.0], [866.0, 3402.0]],
            "source": "ocr",
            "source_image": "back",
            "status": "found",
        },
        {
            "field": "consumer_care",
            "label": "Consumer Care Details",
            "value": "1800 22 4020 | CONSUMER.FEEDBACK@PEPSICO.COM",
            "raw_match": "OR CALL US AT 1800 22 4020 | CONSUMER.FEEDBACK@PEPSICO.COM",
            "confidence": 0.9911,
            "bbox": [[75.0, 375.0], [1487.0, 375.0], [1487.0, 696.0], [75.0, 696.0]],
            "source": "ocr",
            "source_image": "back",
            "status": "found",
        },
        {
            "field": "country_of_origin",
            "label": "Country of Origin",
            "value": None,
            "raw_match": None,
            "confidence": 0.0,
            "bbox": None,
            "source": "ocr",
            "source_image": None,
            "status": "not_found",
        },
        {
            "field": "best_before",
            "label": "Best Before / Use By",
            "value": "07/01/27",
            "raw_match": "25/08/26 & 07/01/27",
            "confidence": 0.998,
            "bbox": [[866.0, 3323.0], [1358.0, 3321.0], [1359.0, 3400.0], [866.0, 3402.0]],
            "source": "ocr",
            "source_image": "back",
            "status": "found",
        },
        {
            "field": "unit_sale_price",
            "label": "Unit Sale Price",
            "value": "₹0.33 / g",
            "raw_match": "Rs. 0.33/- PER g",
            "confidence": 0.9601,
            "bbox": [[860.0, 3182.0], [1335.0, 3192.0], [1333.0, 3282.0], [859.0, 3272.0]],
            "source": "ocr",
            "source_image": "back",
            "status": "found",
        },
    ],
}


def test_lays_adapter_conversion():
    facts = ai_result_to_structured_facts(LAYS_AI_RESULT)
    assert isinstance(facts, StructuredFacts)
    assert facts.overall_confidence > 0.85
    assert facts.fields.net_quantity is not None
    assert facts.fields.net_quantity.value.numeric == 30.5
    assert facts.fields.net_quantity.value.unit == "g"
    assert facts.fields.mrp is not None
    assert facts.fields.mrp.value.amount == 10.0
    assert facts.fields.mrp.value.includes_tax is True


def test_lays_compliance_run():
    facts = ai_result_to_structured_facts(LAYS_AI_RESULT)
    result = run_compliance_checks(facts, retriever=None)
    assert isinstance(result, ComplianceResult)
    assert result.overall_status == "FAIL"  # Missing product name and manufacturer in LAYS_AI_RESULT
    assert result.summary.total_checks == 6
    assert len(result.checks) == 6
    check_map = {c.check_id: c for c in result.checks}
    assert check_map["CHK-01"].status == "FAIL"
    assert check_map["CHK-02"].status == "PASS"
    assert check_map["CHK-03"].status == "PASS"
    assert check_map["CHK-04"].status == "FAIL"
    assert check_map["CHK-05"].status == "PASS"
    assert check_map["CHK-06"].status == "PASS"
