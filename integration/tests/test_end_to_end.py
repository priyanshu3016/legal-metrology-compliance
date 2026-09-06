"""
End-to-end pipeline integration tests:
Real images -> Person 5 AI Engine -> Adapter -> Person 6 Legal Compliance Engine.
"""

import os
import pytest
from integration.orchestrator import run_full_inspection, run_single_image_inspection

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONT = os.path.join(REPO_ROOT, "ai-engine", "samples", "compliant", "demo_product_01_front.jpg")
BACK = os.path.join(REPO_ROOT, "ai-engine", "samples", "compliant", "demo_product_01_back.jpg")
SIDE = os.path.join(REPO_ROOT, "ai-engine", "samples", "compliant", "demo_product_01_side.jpg")


def test_end_to_end_multi_image():
    assert os.path.isfile(FRONT), f"Missing test image: {FRONT}"
    assert os.path.isfile(BACK), f"Missing test image: {BACK}"
    assert os.path.isfile(SIDE), f"Missing test image: {SIDE}"

    result = run_full_inspection(FRONT, BACK, SIDE, use_rag=False)

    assert result["ai_result"] is not None
    assert result["ai_result"]["success"] is True
    assert result["structured_facts"] is not None
    assert result["compliance_result"] is not None

    compliance = result["compliance_result"]
    assert compliance["overall_status"] in {"PASS", "FAIL", "REVIEW"}
    assert len(compliance["checks"]) == 6
    assert "summary" in compliance
    assert compliance["summary"]["total_checks"] == 6


def test_end_to_end_preserves_data():
    result = run_full_inspection(FRONT, BACK, SIDE, demo_mode=True, use_rag=False)

    detections = result["ai_result"]["detections"]
    assert len(detections) >= 7
    for det in detections:
        assert "field" in det
        assert "confidence" in det
        assert "bbox" in det
        assert "status" in det

    checks = result["compliance_result"]["checks"]
    assert len(checks) == 6
    for chk in checks:
        assert "check_id" in chk
        assert "status" in chk
        assert "severity" in chk
        assert "reason" in chk


def test_end_to_end_demo_mode():
    result = run_full_inspection(FRONT, BACK, SIDE, demo_mode=True, use_rag=False)

    assert result["ai_result"]["success"] is True
    assert result["structured_facts"] is not None
    assert result["compliance_result"] is not None
    assert result["compliance_result"]["overall_status"] in {"PASS", "FAIL", "REVIEW"}


def test_end_to_end_single_image():
    result = run_single_image_inspection(FRONT, demo_mode=True, use_rag=False)

    assert result["ai_result"]["success"] is True
    assert result["structured_facts"] is not None
    assert result["compliance_result"] is not None
    assert len(result["compliance_result"]["checks"]) == 6
