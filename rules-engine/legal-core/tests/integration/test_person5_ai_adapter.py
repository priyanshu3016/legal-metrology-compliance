"""
Integration test: Person 5 AI Engine JSON Output -> Person 6 Adapter -> Compliance Checks.

Validates that real-world JSON results produced by Person 5's AI Engine
(e.g., Lay's Potato Chips, Amul Butter from the Integration Handoff Doc)
are seamlessly converted into StructuredFacts and evaluated by the Compliance Engine.
"""

import json
from pathlib import Path
import pytest

from backend.compliance.adapter import (
    ai_result_to_structured_facts,
    polygon_to_bbox,
    parse_net_quantity_str,
    parse_mrp_str,
    parse_date_str,
    parse_consumer_care_str,
    parse_manufacturer_str,
)
from backend.compliance.schemas import StructuredFacts, ComplianceResult
from backend.compliance.engine import run_compliance_checks
from backend.rag.retriever import LegalRetriever


# Person 5's verbatim Lay's output from Section 20 of handoff doc
LAYS_AI_RESULT = {
  "success": True,
  "image_paths": {
    "front": "samples/1.jpg",
    "back": "samples/2.jpg",
    "side": None
  },
  "image_path": "samples/1.jpg",
  "image_id": "1",
  "timestamp": "2026-09-05T16:26:06.123456+00:00",
  "processing_time_ms": 1420,
  "raw_ocr": {
    "front": {
      "full_text": "—COLOU\n&FLAV\nS\nay\nTM\nINDIA'S\nMAGIC MASALA\nMADEWITH\nFINEST POTATOES",
      "line_count": 9,
      "avg_confidence": 0.9904
    },
    "back": {
      "full_text": "OR CALL US AT 1800 22 4020\nCONSUMER.FEEDBACK@PEPSICO.COM\nMRP Rs. 10/- (INCL. OF ALL TAXES)\nUNIT SALE PRICE:\nRs. 0.33/- PER g\n25/08/26 & 07/01/27\nMFD & USE BY:\n30.5 g (28 g+2.5 g)",
      "line_count": 32,
      "avg_confidence": 0.9621
    },
    "side": None
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
      "status": "not_found"
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
      "status": "not_found"
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
      "status": "found"
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
      "status": "found"
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
      "status": "found"
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
      "status": "found"
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
      "status": "not_found"
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
      "status": "found"
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
      "status": "found"
    }
  ]
}

# Person 5's Amul Butter sample from Section 13 of handoff doc
AMUL_AI_RESULT = {
  "success": True,
  "image_paths": {"front": "samples/1.jpg", "back": "samples/2.png", "side": None},
  "image_id": "amul_01",
  "timestamp": "2026-09-05T16:20:00.000000+00:00",
  "raw_ocr": {
    "front": {"full_text": "Amul\nPASTEURISED BUTTER\nuterly butterly delicious", "avg_confidence": 0.98},
    "back": {"full_text": "NetWeight: 200g\nManufactured by: Kaira District Co-operative Milk Producers'Union Ltd., Anand-388 001, India.\nPKD:03/AUG/26\n1800 2583333 | customercare@amul.coop\nT30 USP 0.65/9 EXP:03/AUG/27", "avg_confidence": 0.97}
  },
  "detections": [
    {"field": "product_name", "value": "Amul", "confidence": 0.98, "bbox": [[50.0, 50.0], [300.0, 50.0], [300.0, 150.0], [50.0, 150.0]], "status": "found"},
    {"field": "manufacturer_packer_importer", "value": "Kaira District Co-operative Milk Producers'Union Ltd., Anand-388 001, India.", "confidence": 0.95, "bbox": [[50.0, 200.0], [500.0, 200.0], [500.0, 300.0], [50.0, 300.0]], "status": "found"},
    {"field": "net_quantity", "value": "200 g", "confidence": 0.96, "bbox": [[50.0, 350.0], [200.0, 350.0], [200.0, 400.0], [50.0, 400.0]], "status": "found"},
    {"field": "mrp", "value": None, "confidence": 0.0, "bbox": None, "status": "not_found"},
    {"field": "manufacturing_date", "value": "03/AUG/26", "confidence": 0.97, "bbox": [[50.0, 450.0], [250.0, 450.0], [250.0, 500.0], [50.0, 500.0]], "status": "found"},
    {"field": "consumer_care", "value": "1800 2583333 | customercare@amul.coop", "confidence": 0.94, "bbox": [[50.0, 550.0], [450.0, 550.0], [450.0, 600.0], [50.0, 600.0]], "status": "found"}
  ]
}


def test_adapter_helper_parsers():
    """Unit tests for individual adapter helper parsing functions."""
    # Polygon conversion
    bbox = polygon_to_bbox([[10.0, 20.0], [100.0, 20.0], [100.0, 60.0], [10.0, 60.0]])
    assert bbox is not None
    assert bbox.x == 10
    assert bbox.y == 20
    assert bbox.width == 90
    assert bbox.height == 40

    # Net quantity parsing
    nq = parse_net_quantity_str("30.5 g")
    assert nq is not None and nq.numeric == 30.5 and nq.unit == "g"
    nq2 = parse_net_quantity_str("1.5 L")
    assert nq2 is not None and nq2.numeric == 1.5 and nq2.unit == "l"

    # MRP parsing with tax inclusion detection
    mrp1 = parse_mrp_str("10", raw_match="MRP Rs. 10/- (INCL. OF ALL TAXES)")
    assert mrp1 is not None and mrp1.amount == 10.0 and mrp1.includes_tax is True

    mrp2 = parse_mrp_str("50.00", raw_match="MRP Rs. 50.00")
    assert mrp2 is not None and mrp2.amount == 50.0 and mrp2.includes_tax is False

    # Date parsing (both DD/MM/YY and named month)
    d1 = parse_date_str("25/08/26")
    assert d1 is not None and d1.month == 8 and d1.year == 2026

    d2 = parse_date_str("03/AUG/26")
    assert d2 is not None and d2.month == 8 and d2.year == 2026

    # Consumer care parsing
    care = parse_consumer_care_str("1800 22 4020 | CONSUMER.FEEDBACK@PEPSICO.COM")
    assert care is not None
    assert "1800 22 4020" in care.phone
    assert care.email == "CONSUMER.FEEDBACK@PEPSICO.COM"


def test_person5_lays_integration():
    """
    Validates end-to-end integration with Person 5's Lay's Potato Chips output.
    Expected:
    - CHK-01 FAIL (product name missing in OCR)
    - CHK-02 PASS (30.5 g)
    - CHK-03 PASS (MRP Rs. 10 incl. of all taxes)
    - CHK-04 FAIL (manufacturer missing in OCR)
    - CHK-05 PASS (25/08/26 -> 08/2026)
    - CHK-06 PASS (1800 22 4020, CONSUMER.FEEDBACK@PEPSICO.COM)
    - Overall: FAIL (2 missing declarations)
    """
    facts = ai_result_to_structured_facts(LAYS_AI_RESULT)
    assert isinstance(facts, StructuredFacts)
    assert facts.overall_confidence > 0.85

    result: ComplianceResult = run_compliance_checks(facts, retriever=None)
    check_map = {c.check_id: c for c in result.checks}

    assert check_map["CHK-01"].status == "FAIL", "Missing brand name should FAIL"
    assert check_map["CHK-02"].status == "PASS", "30.5 g should PASS"
    assert check_map["CHK-03"].status == "PASS", "MRP 10 incl. taxes should PASS"
    assert check_map["CHK-04"].status == "FAIL", "Missing manufacturer should FAIL"
    assert check_map["CHK-05"].status == "PASS", "Valid date should PASS"
    assert check_map["CHK-06"].status == "PASS", "Valid consumer care should PASS"

    assert result.overall_status == "FAIL"
    assert result.summary.failed == 2
    assert result.summary.passed == 4


def test_person5_amul_integration():
    """
    Validates end-to-end integration with Person 5's Amul Butter output.
    Expected:
    - CHK-01 PASS (Amul)
    - CHK-02 PASS (200 g)
    - CHK-03 FAIL (MRP stamped flap was not in OCR frame)
    - CHK-04 PASS (Kaira District Co-operative Milk Producers'Union Ltd.)
    - CHK-05 PASS (03/AUG/26 -> 08/2026)
    - CHK-06 PASS (1800 2583333, customercare@amul.coop)
    - Overall: FAIL (due to missing MRP)
    """
    facts = ai_result_to_structured_facts(AMUL_AI_RESULT)
    assert isinstance(facts, StructuredFacts)

    result: ComplianceResult = run_compliance_checks(facts, retriever=None)
    check_map = {c.check_id: c for c in result.checks}

    assert check_map["CHK-01"].status == "PASS"
    assert check_map["CHK-02"].status == "PASS"
    assert check_map["CHK-03"].status == "FAIL", "Missing MRP should FAIL"
    assert check_map["CHK-04"].status == "PASS"
    assert check_map["CHK-05"].status == "PASS"
    assert check_map["CHK-06"].status == "PASS"

    assert result.overall_status == "FAIL"
    assert result.summary.failed == 1
    assert result.summary.passed == 5


def test_person5_integration_with_rag():
    """
    Validates that converted Person 5 facts also successfully attach
    authoritative RAG citations from LegalRetriever.
    """
    retriever = LegalRetriever()
    facts = ai_result_to_structured_facts(AMUL_AI_RESULT)
    result: ComplianceResult = run_compliance_checks(facts, retriever=retriever)

    for c in result.checks:
        assert c.legal_source is not None
        assert c.legal_source.citation
        assert c.legal_source.page > 0
