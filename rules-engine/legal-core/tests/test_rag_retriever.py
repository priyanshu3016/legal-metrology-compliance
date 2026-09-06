"""
Unit and integration tests for LegalRetriever (ChromaDB indexing and retrieval).
"""

import os
import sys
import unittest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.rag.retriever import LegalRetriever, CHECK_QUERIES, RetrievedContext


class TestLegalRetriever(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Use a persistent test directory under backend/data/test_chroma_db
        test_db_dir = os.path.join(WORKSPACE_ROOT, "backend", "data", "test_chroma_db")
        cls.retriever = LegalRetriever(persist_dir=test_db_dir)

    def test_01_collection_populates_141_documents(self):
        """Verify collection has exactly 141 indexed legal chunks."""
        count = self.retriever.collection.count()
        self.assertEqual(count, 141, f"Expected 141 documents in collection, got {count}")

    def test_02_retrieve_chk_03_mrp(self):
        """CHK-03 retrieval must return results containing 'retail sale price' or 'MRP'."""
        results = self.retriever.retrieve_for_check("CHK-03", k=3)
        self.assertEqual(len(results), 3)

        found_mrp = False
        for r in results:
            text_lower = (r.text + " " + r.citation).lower()
            if "retail sale price" in text_lower or "mrp" in text_lower or "maximum retail price" in text_lower:
                found_mrp = True
                break
        self.assertTrue(found_mrp, "CHK-03 results did not contain 'retail sale price' or 'MRP'")

    def test_03_retrieve_chk_06_consumer_care(self):
        """CHK-06 retrieval must return results referencing Rule 6(2)."""
        results = self.retriever.retrieve_for_check("CHK-06", k=3)
        self.assertEqual(len(results), 3)

        found_rule_6_2 = False
        for r in results:
            combined = (r.citation + " " + r.text + " " + str(r.rule) + " " + str(r.sub_rule)).lower()
            if "6(2)" in combined or (r.rule == "6" and r.sub_rule == "2") or "consumer care" in combined:
                found_rule_6_2 = True
                break
        self.assertTrue(found_rule_6_2, "CHK-06 results did not reference Rule 6(2) or consumer care")

    def test_04_all_check_queries_return_results(self):
        """All check queries in CHECK_QUERIES must return non-empty lists with k=3."""
        for check_id in CHECK_QUERIES:
            results = self.retriever.retrieve_for_check(check_id, k=3)
            self.assertEqual(len(results), 3, f"Check {check_id} did not return 3 results")
            for r in results:
                self.assertIsInstance(r, RetrievedContext)
                self.assertTrue(r.citation, f"Check {check_id} returned empty citation")
                self.assertGreater(r.page, 0, f"Check {check_id} returned invalid page {r.page}")
                self.assertTrue(r.text.strip(), f"Check {check_id} returned empty text")
                self.assertTrue(r.document.endswith(".pdf"), f"Invalid document: {r.document}")

    def test_05_metadata_fields_preserved(self):
        """Retrieved context must preserve document, page, rule, citation, and distance."""
        results = self.retriever.retrieve_raw("Rule 6 declarations to be made on every package", k=3)
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIn(r.document, ["rules2011.pdf", "rules2009.pdf"])
            self.assertGreaterEqual(r.page, 1)
            self.assertIsInstance(r.distance, float)


if __name__ == "__main__":
    unittest.main(verbosity=2)
