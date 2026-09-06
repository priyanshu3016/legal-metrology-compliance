"""
Unit and integration tests for Compliance Engine Orchestrator.
"""

import json
import os
import sys
import unittest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.compliance.schemas import StructuredFacts, ComplianceResult
from backend.compliance.engine import run_compliance_checks
from backend.rag.retriever import LegalRetriever


def load_fixture(name: str) -> StructuredFacts:
    path = os.path.join(WORKSPACE_ROOT, "tests", "golden_data", f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return StructuredFacts(**data)


class TestComplianceEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_db_dir = os.path.join(WORKSPACE_ROOT, "backend", "data", "test_chroma_db")
        cls.retriever = LegalRetriever(persist_dir=test_db_dir)

    def setUp(self):
        self.compliant_facts = load_fixture("compliant_biscuit")
        self.missing_mrp_facts = load_fixture("missing_mrp")
        self.mrp_no_tax_facts = load_fixture("mrp_no_tax")
        self.blurry_facts = load_fixture("blurry_low_conf")

    def test_01_compliant_biscuit_engine_evaluation(self):
        """Compliant fixture should yield overall PASS and 100% score."""
        res: ComplianceResult = run_compliance_checks(self.compliant_facts, retriever=None)
        self.assertEqual(res.overall_status, "PASS")
        self.assertEqual(res.automated_check_score, 100.0)
        self.assertEqual(res.compliance_score, 100.0)
        self.assertEqual(res.summary.total_checks, 6)
        self.assertEqual(res.summary.passed, 6)
        self.assertEqual(res.summary.failed, 0)
        self.assertEqual(res.summary.review, 0)
        self.assertGreater(len(res.disclaimers), 0)

    def test_02_missing_mrp_engine_evaluation(self):
        """Missing MRP should yield overall FAIL and < 100% score."""
        res: ComplianceResult = run_compliance_checks(self.missing_mrp_facts, retriever=None)
        self.assertEqual(res.overall_status, "FAIL")
        self.assertEqual(res.summary.failed, 1)
        self.assertEqual(res.summary.passed, 5)
        self.assertEqual(res.automated_check_score, 83.3)

    def test_03_mrp_no_tax_engine_evaluation(self):
        """MRP without tax declaration should yield overall FAIL."""
        res: ComplianceResult = run_compliance_checks(self.mrp_no_tax_facts, retriever=None)
        self.assertEqual(res.overall_status, "FAIL")
        self.assertEqual(res.summary.failed, 1)
        self.assertEqual(res.summary.passed, 5)

    def test_04_blurry_photo_engine_evaluation(self):
        """Low confidence blurry image should yield overall REVIEW."""
        res: ComplianceResult = run_compliance_checks(self.blurry_facts, retriever=None)
        self.assertEqual(res.overall_status, "REVIEW")
        self.assertEqual(res.summary.review, 6)
        self.assertEqual(res.summary.failed, 0)
        self.assertEqual(res.summary.passed, 0)
        self.assertEqual(res.automated_check_score, 0.0)

    def test_05_engine_with_retriever_citations(self):
        """Running engine with retriever attaches valid citations to all check results."""
        res: ComplianceResult = run_compliance_checks(self.compliant_facts, retriever=self.retriever)
        self.assertEqual(len(res.checks), 6)

        for c in res.checks:
            self.assertIsNotNone(c.legal_source, f"Check {c.check_id} missing legal source citation")
            self.assertTrue(c.legal_source.citation, f"Check {c.check_id} has empty citation")
            self.assertGreater(c.legal_source.page, 0, f"Check {c.check_id} has invalid page number")
            self.assertTrue(c.legal_source.text, f"Check {c.check_id} has empty legal text")

    def test_06_json_serialization_validity(self):
        """Verify ComplianceResult serializes to valid JSON matching API contract."""
        res: ComplianceResult = run_compliance_checks(self.compliant_facts, retriever=self.retriever)
        json_str = res.model_dump_json(indent=2)
        self.assertTrue(len(json_str) > 0)
        loaded = json.loads(json_str)
        self.assertEqual(loaded["inspection_id"], self.compliant_facts.inspection_id)
        self.assertEqual(loaded["overall_status"], "PASS")
        self.assertEqual(loaded["automated_check_score"], 100.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
