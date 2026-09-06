"""
End-to-End Pipeline Tests for analyzer.py
Verifies complete image analysis, error resilience, and schema compliance.
"""

import os
import pytest
from analyzer import analyze_image, analyze_multi_image
from schemas import validate_result_schema


SAMPLE_IMAGE = "samples/compliant/sample_test_label.jpg"


def test_analyze_valid_image():
    """Verify end-to-end analysis on valid test image succeeds and conforms to schema."""
    assert os.path.exists(SAMPLE_IMAGE)
    result = analyze_image(SAMPLE_IMAGE)

    assert result["success"] is True
    assert result["image_path"] == SAMPLE_IMAGE
    assert result["image_id"] == "sample_test_label"
    assert result["processing_time_ms"] > 0
    assert len(result["detections"]) == 9
    assert result["raw_ocr"] is not None
    assert result["raw_ocr"]["line_count"] >= 4
    assert result["readability"] is not None
    assert result["readability"]["estimated_readability"] in ("good", "moderate", "poor")
    assert result["errors"] == []

    is_valid, validation_errors = validate_result_schema(result)
    assert is_valid is True, f"Schema validation failed: {validation_errors}"


def test_analyze_nonexistent_file():
    """Verify non-existent file path returns structured IMAGE_NOT_FOUND error."""
    result = analyze_image("samples/does_not_exist_123.png")

    assert result["success"] is False
    assert len(result["errors"]) == 1
    assert result["errors"][0]["code"] == "IMAGE_NOT_FOUND"
    assert len(result["detections"]) == 9
    for d in result["detections"]:
        assert d["status"] == "not_found"

    is_valid, validation_errors = validate_result_schema(result)
    assert is_valid is True


def test_analyze_unsupported_file():
    """Verify unsupported file type returns structured UNSUPPORTED_FORMAT error."""
    dummy_txt = "samples/test_document.pdf"
    with open(dummy_txt, "w") as f:
        f.write("test content")

    try:
        result = analyze_image(dummy_txt)
        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["code"] == "UNSUPPORTED_FORMAT"
    finally:
        if os.path.exists(dummy_txt):
            os.remove(dummy_txt)


def test_analyze_never_raises_exceptions():
    """Verify invalid inputs (None, empty string, etc.) never raise uncaught exceptions."""
    try:
        res1 = analyze_image("")
        assert res1["success"] is False
        res2 = analyze_image(None)
        assert res2["success"] is False
    except Exception as e:
        pytest.fail(f"analyze_image raised an unexpected exception: {e}")


def test_analyze_demo_mode_explicit():
    """Verify explicit demo mode returns pre-verified ground truth without executing OCR."""
    result = analyze_image("samples/compliant/demo_product_01.jpg", demo_mode=True)
    assert result["success"] is True
    assert result["metadata"]["demo_mode"] is True
    assert len(result["detections"]) == 9

    field_map = {d["field"]: d for d in result["detections"]}
    assert field_map["mrp"]["status"] == "found"
    assert field_map["mrp"]["value"] == "20.00"
    assert field_map["mrp"]["source"] == "demo_fallback"


def test_analyze_demo_mode_noncompliant():
    """Verify demo fallback for non-compliant image flags missing field properly."""
    result = analyze_image("samples/noncompliant/demo_product_06.jpg", demo_mode=True)
    assert result["success"] is True
    assert result["metadata"]["demo_mode"] is True

    field_map = {d["field"]: d for d in result["detections"]}
    # Product 06 demo specifically has missing MRP
    assert field_map["mrp"]["status"] == "not_found"
    assert field_map["mrp"]["value"] is None
    assert field_map["net_quantity"]["status"] == "found"


def test_all_ten_demo_samples_exist_and_validate():
    """Verify all 10 demo product images exist on disk and pass end-to-end analysis."""
    demo_files = [
        "samples/compliant/demo_product_01.jpg",
        "samples/compliant/demo_product_02.jpg",
        "samples/compliant/demo_product_03.jpg",
        "samples/compliant/demo_product_04.jpg",
        "samples/compliant/demo_product_05.jpg",
        "samples/noncompliant/demo_product_06.jpg",
        "samples/noncompliant/demo_product_07.jpg",
        "samples/noncompliant/demo_product_08.jpg",
        "samples/noncompliant/demo_product_09.jpg",
        "samples/noncompliant/demo_product_10.jpg",
    ]

    for path in demo_files:
        assert os.path.exists(path), f"Missing demo image: {path}"
        result = analyze_image(path)
        assert result["success"] is True, f"Failed on {path}: {result.get('errors')}"
        assert len(result["detections"]) == 9
        is_valid, validation_errors = validate_result_schema(result)
        assert is_valid is True, f"Schema error on {path}: {validation_errors}"


# --------------------------------------------------------------------------
# Multi-Image Inspection Tests
# --------------------------------------------------------------------------

def test_multi_image_front_back():
    """Two-image inspection returns valid result."""
    result = analyze_multi_image(
        front_image_path="samples/compliant/demo_product_01.jpg",
        back_image_path="samples/compliant/demo_product_02.jpg"
    )
    assert result["success"] is True
    assert "image_paths" in result
    assert result["image_paths"]["front"] == "samples/compliant/demo_product_01.jpg"
    assert result["image_paths"]["back"] == "samples/compliant/demo_product_02.jpg"
    assert result["image_paths"]["side"] is None
    assert len(result["detections"]) == 9
    is_valid, val_errs = validate_result_schema(result)
    assert is_valid is True, f"Schema error: {val_errs}"


def test_multi_image_with_side():
    """Three-image inspection returns valid result."""
    result = analyze_multi_image(
        front_image_path="samples/compliant/demo_product_01.jpg",
        back_image_path="samples/compliant/demo_product_02.jpg",
        side_image_path="samples/compliant/demo_product_03.jpg"
    )
    assert result["success"] is True
    assert "side" in result["image_paths"]
    assert result["image_paths"]["side"] is not None
    assert len(result["detections"]) == 9
    is_valid, val_errs = validate_result_schema(result)
    assert is_valid is True, f"Schema error: {val_errs}"


def test_multi_image_side_none():
    """Missing side image is not an error."""
    result = analyze_multi_image(
        front_image_path="samples/compliant/demo_product_01.jpg",
        back_image_path="samples/compliant/demo_product_02.jpg",
        side_image_path=None
    )
    assert result["success"] is True
    assert result["image_paths"]["side"] is None


def test_multi_image_missing_front():
    """Missing front image is an error."""
    result = analyze_multi_image(
        front_image_path="/nonexistent/front.jpg",
        back_image_path="samples/compliant/demo_product_02.jpg"
    )
    assert result["success"] is False
    assert len(result["errors"]) >= 1


def test_multi_image_readability_per_image():
    """Readability is reported per image, not combined."""
    result = analyze_multi_image(
        front_image_path="samples/compliant/demo_product_01.jpg",
        back_image_path="samples/compliant/demo_product_02.jpg"
    )
    assert "front" in result["readability"]
    assert "back" in result["readability"]
    assert result["readability"]["front"] is not None
    assert result["readability"]["back"] is not None
    assert result["readability"]["side"] is None


def test_multi_image_detections_have_source_image():
    """Every detection has source_image key set."""
    result = analyze_multi_image(
        front_image_path="samples/compliant/demo_product_01.jpg",
        back_image_path="samples/compliant/demo_product_02.jpg"
    )
    for det in result["detections"]:
        assert "source_image" in det


def test_multi_image_demo_mode():
    """Verify multi-image demo fallback returns structured data instantly."""
    result = analyze_multi_image(
        front_image_path="samples/compliant/demo_product_01_front.jpg",
        back_image_path="samples/compliant/demo_product_01_back.jpg",
        side_image_path="samples/compliant/demo_product_01_side.jpg",
        demo_mode=True
    )
    assert result["success"] is True
    assert result["metadata"]["demo_mode"] is True
    assert len(result["detections"]) == 9
    assert result["image_paths"]["front"] == "samples/compliant/demo_product_01_front.jpg"
    assert result["image_paths"]["side"] == "samples/compliant/demo_product_01_side.jpg"
    is_valid, errs = validate_result_schema(result)
    assert is_valid is True, f"Schema error: {errs}"




