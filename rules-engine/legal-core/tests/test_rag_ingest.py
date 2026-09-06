"""
Automated unit & integration verification for RAG Ingestion (rag/ingest.py).

Verifies:
1. Both legal PDFs are read and exist
2. Pages are extracted accurately (rules2011: 43 pages, rules2009: 18 pages)
3. Chunks are created with rule-aware boundaries
4. Metadata contains page, document, rule, and citation info
5. No empty or whitespace-only chunks are produced
6. All core compliance check anchors (CHK-01 to CHK-07, CHK-09, Sec 18, Sec 36) exist
7. ChromaDB batch formatting works with valid data types
"""

import os
import sys
import unittest

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.rag.ingest import (
    resolve_pdf_paths,
    extract_pages_from_pdf,
    ingest_documents,
    prepare_chroma_batches,
    DOC_TITLES
)


class TestRAGIngestion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path_2009, cls.path_2011 = resolve_pdf_paths(WORKSPACE_ROOT)
        cls.chunks = ingest_documents(WORKSPACE_ROOT)
        cls.chunk_map = {c.chunk_id: c for c in cls.chunks}

    def test_01_both_pdfs_exist_and_resolve(self):
        """Verify both source PDFs exist and are resolved in legal_docs/."""
        self.assertTrue(os.path.exists(self.path_2009), f"Missing 2009 PDF at {self.path_2009}")
        self.assertTrue(os.path.exists(self.path_2011), f"Missing 2011 PDF at {self.path_2011}")
        self.assertTrue(self.path_2009.endswith(os.path.join("legal_docs", "rules2009.pdf")))
        self.assertTrue(self.path_2011.endswith(os.path.join("legal_docs", "rules2011.pdf")))

    def test_02_page_extraction_counts(self):
        """Verify exact page count extraction via PyMuPDF."""
        pages_2011 = extract_pages_from_pdf(self.path_2011)
        self.assertEqual(len(pages_2011), 43, "rules2011.pdf must contain exactly 43 pages")

        pages_2009 = extract_pages_from_pdf(self.path_2009)
        self.assertEqual(len(pages_2009), 18, "rules2009.pdf must contain exactly 18 pages")

    def test_03_chunks_created_and_no_empty_chunks(self):
        """Verify chunks count > 0 and no chunk text or ID is empty."""
        self.assertGreater(len(self.chunks), 100, "Should produce at least 100 granular legal chunks")
        for chunk in self.chunks:
            self.assertTrue(chunk.chunk_id, "Every chunk must have a non-empty chunk_id")
            self.assertTrue(chunk.text.strip(), f"Chunk {chunk.chunk_id} text cannot be empty")
            self.assertGreater(len(chunk.text.strip()), 20, f"Chunk {chunk.chunk_id} text too short")

    def test_04_metadata_completeness(self):
        """Verify metadata fields conform to MVP_BUILD_SPEC schema."""
        for chunk in self.chunks:
            m = chunk.metadata
            self.assertIn(m.document, ["rules2011.pdf", "rules2009.pdf"])
            self.assertEqual(m.document, m.document_name)
            self.assertIn(m.document_title, list(DOC_TITLES.values()))
            self.assertIsInstance(m.page, int)
            self.assertGreaterEqual(m.page, 1)
            self.assertEqual(m.page, m.page_number)
            self.assertTrue(m.chunk_type, f"Missing chunk_type in {chunk.chunk_id}")
            self.assertTrue(m.title, f"Missing title in {chunk.chunk_id}")
            self.assertTrue(m.citation, f"Missing citation in {chunk.chunk_id}")

    def test_05_core_compliance_anchors_present(self):
        """Verify chunks required for CHK-01 through CHK-07 and CHK-09 are specifically present."""
        expected_anchors = {
            "rules2011_rule6_1_b": {"rule": "6", "sub": "1", "clause": "b", "page": 5},
            "rules2011_rule6_1_c": {"rule": "6", "sub": "1", "clause": "c", "page": 5},
            "rules2011_rule6_1_e": {"rule": "6", "sub": "1", "clause": "e", "page": 6},
            "rules2011_rule6_1_a": {"rule": "6", "sub": "1", "clause": "a", "page": 5},
            "rules2011_rule6_1_d": {"rule": "6", "sub": "1", "clause": "d", "page": 5},
            "rules2011_rule6_2":   {"rule": "6", "sub": "2", "clause": None, "page": 7},
            "rules2011_rule12_6":  {"rule": "12", "sub": "6", "clause": None, "page": 13},
            "rules2011_rule2_m":   {"rule": "2", "sub": None, "clause": "m", "page": 3},
            "rules2009_sec18":     {"rule": "18", "sub": None, "clause": None, "page": 8},
            "rules2009_sec36":     {"rule": "36", "sub": None, "clause": None, "page": 11},
        }

        for cid, expected in expected_anchors.items():
            self.assertIn(cid, self.chunk_map, f"Missing required compliance anchor chunk: {cid}")
            chunk = self.chunk_map[cid]
            if expected["rule"] is not None:
                self.assertEqual(chunk.metadata.rule, expected["rule"])
            if expected["sub"] is not None:
                self.assertEqual(chunk.metadata.sub_rule, expected["sub"])
            if expected["clause"] is not None:
                self.assertEqual(chunk.metadata.clause, expected["clause"])
            self.assertEqual(chunk.metadata.page, expected["page"])

    def test_06_chromadb_batch_preparation(self):
        """Verify ChromaDB batch formatting produces valid arrays with no None values."""
        batch = prepare_chroma_batches(self.chunks)
        self.assertEqual(len(batch["ids"]), len(self.chunks))
        self.assertEqual(len(batch["documents"]), len(self.chunks))
        self.assertEqual(len(batch["metadatas"]), len(self.chunks))

        # Test ChromaDB metadata constraints: must not contain None
        for meta in batch["metadatas"]:
            for k, v in meta.items():
                self.assertIsNotNone(v, f"ChromaDB metadata key '{k}' has forbidden None value")
                self.assertIsInstance(v, (str, int, float, bool), f"Invalid ChromaDB type for key '{k}'")


if __name__ == "__main__":
    unittest.main(verbosity=2)
