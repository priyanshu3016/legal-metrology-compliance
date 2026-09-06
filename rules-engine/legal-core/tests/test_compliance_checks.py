"""
Unit tests for deterministic compliance checks (CHK-01 to CHK-06).
"""

import json
import os
import sys
import unittest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.compliance.schemas import StructuredFacts, CheckResult
from backend.compliance.checks import (
    CORE_CHECKS,
    check_product_name,
    check_net_quantity,
    check_mrp,
    check_manufacturer,
    check_manufacturing_date,
    check_consumer_care,
)


def load_fixture(name: str) -> StructuredFacts:
    path = os.path.join(WORKSPACE_ROOT, "tests", "golden_data", f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return StructuredFacts(**data)


class TestComplianceChecks(unittest.TestCase):

    def setUp(self):
        self.compliant_facts = load_fixture("compliant_biscuit")
        self.missing_mrp_facts = load_fixture("missing_mrp")
        self.mrp_no_tax_facts = load_fixture("mrp_no_tax")
        self.blurry_facts = load_fixture("blurry_low_conf")

    def test_01_compliant_biscuit_all_pass(self):
        """On compliant biscuit, all 6 core checks must return PASS."""
        for check_id, check_fn in CORE_CHECKS.items():
            result: CheckResult = check_fn(self.compliant_facts)
            self.assertEqual(result.status, "PASS", f"{check_id} failed on compliant data: {result.reason}")
            self.assertTrue(result.reason, f"{check_id} has empty reason")
            self.assertIsNotNone(result.detected_value, f"{check_id} has null detected_value")
            self.assertIsNotNone(result.evidence, f"{check_id} missing evidence")

    def test_02_missing_mrp_fails_chk_03(self):
        """On missing_mrp fixture, CHK-03 must return FAIL and other checks PASS."""
        res_mrp = check_mrp(self.missing_mrp_facts)
        self.assertEqual(res_mrp.status, "FAIL", "CHK-03 should FAIL when MRP is missing")
        self.assertEqual(res_mrp.severity, "CRITICAL")
        self.assertIn("missing", res_mrp.reason.lower())

        # Verify other 5 checks still pass
        for cid in ["CHK-01", "CHK-02", "CHK-04", "CHK-05", "CHK-06"]:
            r = CORE_CHECKS[cid](self.missing_mrp_facts)
            self.assertEqual(r.status, "PASS", f"{cid} unexpectedly failed on missing_mrp fixture")

    def test_03_mrp_no_tax_fails_chk_03(self):
        """On mrp_no_tax fixture, CHK-03 must return FAIL due to missing tax declaration."""
        res_mrp = check_mrp(self.mrp_no_tax_facts)
        self.assertEqual(res_mrp.status, "FAIL", "CHK-03 should FAIL when tax declaration is missing")
        self.assertIn("inclusive of all taxes", res_mrp.reason.lower())

    def test_04_blurry_fixture_triggers_review(self):
        """On blurry fixture with confidence < 0.70, checks must return REVIEW."""
        for check_id, check_fn in CORE_CHECKS.items():
            result = check_fn(self.blurry_facts)
            self.assertEqual(result.status, "REVIEW", f"{check_id} should be REVIEW for low confidence photo")
            self.assertIn("below 0.70", result.reason.lower())

    def test_05_check_severities_match_spec(self):
        """Verify severity levels align with RULE_MATRIX."""
        res_01 = check_product_name(self.compliant_facts)
        res_02 = check_net_quantity(self.compliant_facts)
        res_03 = check_mrp(self.compliant_facts)
        res_04 = check_manufacturer(self.compliant_facts)
        res_05 = check_manufacturing_date(self.compliant_facts)
        res_06 = check_consumer_care(self.compliant_facts)

        self.assertEqual(res_01.severity, "CRITICAL")
        self.assertEqual(res_02.severity, "CRITICAL")
        self.assertEqual(res_03.severity, "CRITICAL")
        self.assertEqual(res_04.severity, "CRITICAL")
        self.assertEqual(res_05.severity, "HIGH")
        self.assertEqual(res_06.severity, "HIGH")


if __name__ == "__main__":
    unittest.main(verbosity=2)
