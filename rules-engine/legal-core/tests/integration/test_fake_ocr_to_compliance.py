"""
Integration test: Simulated Person 5 OCR structured facts to Person 6 Compliance Engine.

Verifies end-to-end deterministic evaluation on simulated OCR facts without
external OCR or LLM dependencies.
"""

import json
from pathlib import Path
import pytest

from backend.compliance.schemas import StructuredFacts, ComplianceResult
from backend.compliance.engine import run_compliance_checks

FIXTURES_DIR = Path(__file__).resolve().parent / "fake_ocr"


def load_simulated_ocr_facts(filename: str) -> StructuredFacts:
    filepath = FIXTURES_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return StructuredFacts(**data)


def print_inspection_summary(case_title: str, result: ComplianceResult):
    print(f"\n{'=' * 60}")
    print(f"CASE: {case_title}")
    print(f"{'=' * 60}")
    print(f"Overall Status:        {result.overall_status}")
    print(f"Automated Check Score: {result.automated_check_score:.1f}%")
    print(f"Summary:               Passed: {result.summary.passed} | Failed: {result.summary.failed} | Review: {result.summary.review}")
    print("Checks:")
    for c in result.checks:
        conf_str = f"{c.confidence:.2f}" if c.confidence is not None else "N/A"
        print(f"  [{c.status:<6}] {c.check_id:<6} {c.rule_name:<38} (conf: {conf_str}) -> {c.reason}")


def test_01_compliant_fake_ocr():
    """
    Case 1: Fully compliant packaging facts extracted by OCR.
    Expected: CHK-01 through CHK-06 PASS, overall PASS, score 100%.
    """
    facts = load_simulated_ocr_facts("compliant.json")
    result = run_compliance_checks(facts, retriever=None)
    print_inspection_summary("Compliant Simulated OCR Facts", result)

    check_statuses = {c.check_id: c.status for c in result.checks}

    # Assert individual checks
    assert check_statuses["CHK-01"] == "PASS", f"CHK-01 expected PASS, got {check_statuses['CHK-01']}"
    assert check_statuses["CHK-02"] == "PASS", f"CHK-02 expected PASS, got {check_statuses['CHK-02']}"
    assert check_statuses["CHK-03"] == "PASS", f"CHK-03 expected PASS, got {check_statuses['CHK-03']}"
    assert check_statuses["CHK-04"] == "PASS", f"CHK-04 expected PASS, got {check_statuses['CHK-04']}"
    assert check_statuses["CHK-05"] == "PASS", f"CHK-05 expected PASS, got {check_statuses['CHK-05']}"
    assert check_statuses["CHK-06"] == "PASS", f"CHK-06 expected PASS, got {check_statuses['CHK-06']}"

    # Assert overall outcome
    assert result.overall_status == "PASS"
    assert result.automated_check_score == 100.0
    assert result.summary.passed == 6
    assert result.summary.failed == 0
    assert result.summary.review == 0


def test_02_missing_mrp_fake_ocr():
    """
    Case 2: Simulated OCR where MRP is absent from package.
    Expected: CHK-03 FAIL, overall FAIL.
    """
    facts = load_simulated_ocr_facts("missing_mrp.json")
    result = run_compliance_checks(facts, retriever=None)
    print_inspection_summary("Missing MRP Simulated OCR Facts", result)

    check_statuses = {c.check_id: c.status for c in result.checks}

    # Assert CHK-03 is FAIL
    assert check_statuses["CHK-03"] == "FAIL", f"CHK-03 expected FAIL, got {check_statuses['CHK-03']}"

    # Assert other checks pass
    assert check_statuses["CHK-01"] == "PASS"
    assert check_statuses["CHK-02"] == "PASS"
    assert check_statuses["CHK-04"] == "PASS"
    assert check_statuses["CHK-05"] == "PASS"
    assert check_statuses["CHK-06"] == "PASS"

    # Assert overall status is FAIL
    assert result.overall_status == "FAIL"
    assert result.summary.failed == 1
    assert result.summary.passed == 5


def test_03_low_confidence_fake_ocr():
    """
    Case 3: Simulated OCR with low confidence / blurry photo (<0.70).
    Expected: Low-confidence checks become REVIEW, overall REVIEW.
    """
    facts = load_simulated_ocr_facts("low_confidence.json")
    result = run_compliance_checks(facts, retriever=None)
    print_inspection_summary("Low Confidence Simulated OCR Facts", result)

    check_statuses = {c.check_id: c.status for c in result.checks}

    # Assert low-confidence checks become REVIEW
    for cid in ["CHK-01", "CHK-02", "CHK-03", "CHK-04", "CHK-05", "CHK-06"]:
        assert check_statuses[cid] == "REVIEW", f"{cid} expected REVIEW, got {check_statuses[cid]}"

    # Assert overall status is REVIEW
    assert result.overall_status == "REVIEW"
    assert result.summary.review == 6
    assert result.summary.failed == 0
    assert result.summary.passed == 0
    assert result.automated_check_score == 0.0
