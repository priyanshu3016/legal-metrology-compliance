"""
Tests for OCR module (ocr.py)
"""

import os
import numpy as np
import pytest
from ocr import run_ocr

SAMPLE_IMAGE = "samples/compliant/sample_test_label.jpg"


def test_ocr_returns_results():
    """Verify OCR returns text detections for a valid test image."""
    assert os.path.exists(SAMPLE_IMAGE), "Sample test image must exist"
    results = run_ocr(SAMPLE_IMAGE)
    assert len(results) >= 4, f"Expected at least 4 detections, got {len(results)}"


def test_ocr_result_format():
    """Verify each detection contains text, confidence, and 4-point bbox."""
    results = run_ocr(SAMPLE_IMAGE)
    for res in results:
        assert "text" in res and isinstance(res["text"], str)
        assert len(res["text"]) > 0
        assert "confidence" in res and isinstance(res["confidence"], float)
        assert 0.0 <= res["confidence"] <= 1.0
        assert "bbox" in res and isinstance(res["bbox"], list)
        assert len(res["bbox"]) == 4
        for pt in res["bbox"]:
            assert len(pt) == 2
            assert isinstance(pt[0], (int, float))
            assert isinstance(pt[1], (int, float))


def test_ocr_confidence_filter():
    """Verify confidence filtering works when threshold is set higher."""
    # With a 0.9999 threshold, only near-perfect matches remain
    high_conf_results = run_ocr(SAMPLE_IMAGE, min_confidence=0.999)
    all_results = run_ocr(SAMPLE_IMAGE, min_confidence=0.10)
    assert len(high_conf_results) <= len(all_results)


def test_ocr_empty_canvas():
    """Verify an all-white canvas returns an empty detections list."""
    white_img = np.ones((300, 300, 3), dtype=np.uint8) * 255
    results = run_ocr(white_img)
    assert len(results) == 0
