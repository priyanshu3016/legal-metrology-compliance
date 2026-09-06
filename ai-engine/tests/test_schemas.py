"""
Tests for data contract and schema definitions (schemas.py)
"""

from schemas import (
    create_empty_detection,
    create_detection,
    create_error,
    create_analysis_result,
    create_multi_analysis_result,
    validate_result_schema,
    STATUS_FOUND,
    STATUS_LOW_CONFIDENCE,
    STATUS_NOT_FOUND,
    STATUS_AMBIGUOUS
)
from config import FIELD_MRP, MANDATORY_FIELDS



def test_create_empty_detection():
    """Verify empty detection has correct defaults and 'not_found' status."""
    det = create_empty_detection(FIELD_MRP)
    assert det["field"] == FIELD_MRP
    assert det["value"] is None
    assert det["confidence"] == 0.0
    assert det["bbox"] is None
    assert det["status"] == STATUS_NOT_FOUND


def test_create_detection_found():
    """Verify detection with confidence >= threshold receives 'found' status."""
    bbox = [[10.0, 20.0], [50.0, 20.0], [50.0, 40.0], [10.0, 40.0]]
    det = create_detection(FIELD_MRP, "120.00", "MRP Rs. 120.00", 0.95, bbox)
    assert det["field"] == FIELD_MRP
    assert det["value"] == "120.00"
    assert det["raw_match"] == "MRP Rs. 120.00"
    assert det["confidence"] == 0.95
    assert det["bbox"] == bbox
    assert det["status"] == STATUS_FOUND


def test_create_detection_low_confidence():
    """Verify detection with confidence < threshold receives 'low_confidence' status."""
    det = create_detection(FIELD_MRP, "120.00", "MRP 120", 0.45, None, confidence_threshold=0.60)
    assert det["status"] == STATUS_LOW_CONFIDENCE


def test_create_analysis_result_structure():
    """Verify complete analysis result adheres to contract schema."""
    res = create_analysis_result(
        image_path="/path/to/test.jpg",
        image_id="test_01",
        processing_time_ms=120
    )
    assert res["success"] is True
    assert res["image_path"] == "/path/to/test.jpg"
    assert res["image_id"] == "test_01"
    assert len(res["detections"]) == len(MANDATORY_FIELDS)
    assert res["errors"] == []

    is_valid, validation_errors = validate_result_schema(res)
    assert is_valid is True
    assert len(validation_errors) == 0


def test_create_error_result():
    """Verify error result has success=False and contains the error."""
    err = create_error("IMAGE_NOT_FOUND", "Could not find image")
    res = create_analysis_result(
        image_path="/path/to/missing.jpg",
        errors=[err]
    )
    assert res["success"] is False
    assert len(res["errors"]) == 1
    assert res["errors"][0]["code"] == "IMAGE_NOT_FOUND"

    is_valid, _ = validate_result_schema(res)
    assert is_valid is True


def test_create_detection_with_source_image():
    det = create_detection("mrp", "120.00", "MRP Rs. 120.00", 0.95,
                           [[0, 0], [100, 0], [100, 30], [0, 30]],
                           source_image="back")
    assert det["source_image"] == "back"
    assert det["status"] == STATUS_FOUND


def test_create_empty_detection_has_source_image():
    det = create_empty_detection("mrp")
    assert "source_image" in det
    assert det["source_image"] is None


def test_create_multi_analysis_result_structure():
    result = create_multi_analysis_result(
        image_paths={"front": "/a.jpg", "back": "/b.jpg", "side": None}
    )
    assert result["success"] is True
    assert "image_paths" in result
    assert result["image_paths"]["front"] == "/a.jpg"
    assert result["image_paths"]["side"] is None
    assert "image_path" in result  # backward compat
    is_valid, validation_errors = validate_result_schema(result)
    assert is_valid is True
    assert len(validation_errors) == 0

