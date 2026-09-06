"""
Data schemas and builders for the Legal Metrology Compliance AI Engine.
Standardized contract consumed by Backend (Person 3) and Rules Engine (Person 6).
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from config import MANDATORY_FIELDS, FIELD_LABELS


# Valid detection statuses
STATUS_FOUND = "found"
STATUS_LOW_CONFIDENCE = "low_confidence"
STATUS_NOT_FOUND = "not_found"
STATUS_AMBIGUOUS = "ambiguous"

VALID_STATUSES = {STATUS_FOUND, STATUS_LOW_CONFIDENCE, STATUS_NOT_FOUND, STATUS_AMBIGUOUS}


def create_empty_detection(field_name: str) -> Dict[str, Any]:
    """Create a default 'not_found' detection dictionary for a mandatory field."""
    return {
        "field": field_name,
        "label": FIELD_LABELS.get(field_name, field_name),
        "value": None,
        "raw_match": None,
        "confidence": 0.0,
        "bbox": None,
        "source": "ocr",
        "source_image": None,
        "status": STATUS_NOT_FOUND
    }


def create_detection(
    field_name: str,
    value: Optional[str],
    raw_match: Optional[str],
    confidence: float,
    bbox: Optional[List[List[float]]],
    source: str = "ocr",
    confidence_threshold: float = 0.60,
    source_image: Optional[str] = None
) -> Dict[str, Any]:
    """Create a populated detection dictionary with appropriate status."""
    if not value or confidence <= 0.0:
        det = create_empty_detection(field_name)
        det["source_image"] = source_image
        return det

    status = STATUS_FOUND if confidence >= confidence_threshold else STATUS_LOW_CONFIDENCE

    return {
        "field": field_name,
        "label": FIELD_LABELS.get(field_name, field_name),
        "value": str(value).strip(),
        "raw_match": str(raw_match).strip() if raw_match else str(value).strip(),
        "confidence": round(float(confidence), 4),
        "bbox": bbox,
        "source": source,
        "source_image": source_image,
        "status": status
    }


def create_error(code: str, message: str) -> Dict[str, str]:
    """Create a standardized error dictionary."""
    return {
        "code": code,
        "message": message
    }


def create_analysis_result(
    image_path: str,
    image_id: Optional[str] = None,
    raw_ocr: Optional[Dict[str, Any]] = None,
    detections: Optional[List[Dict[str, Any]]] = None,
    readability: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    errors: Optional[List[Dict[str, str]]] = None,
    processing_time_ms: int = 0
) -> Dict[str, Any]:
    """
    Construct the final JSON response compliant with the data contract.
    """
    errors_list = errors or []
    success = len(errors_list) == 0

    return {
        "success": success,
        "image_path": image_path,
        "image_id": image_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processing_time_ms": processing_time_ms,
        "raw_ocr": raw_ocr,
        "detections": detections or [create_empty_detection(f) for f in MANDATORY_FIELDS],
        "readability": readability,
        "metadata": metadata or {},
        "errors": errors_list
    }


def create_multi_analysis_result(
    image_paths: Dict[str, Optional[str]],
    image_id: Optional[str] = None,
    raw_ocr: Optional[Dict[str, Any]] = None,
    detections: Optional[List[Dict[str, Any]]] = None,
    readability: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    errors: Optional[List[Dict[str, str]]] = None,
    processing_time_ms: int = 0
) -> Dict[str, Any]:
    """
    Construct the multi-image JSON response compliant with the data contract.
    Contains image_paths dict and preserves image_path (set to front) for backward compatibility.
    """
    errors_list = errors or []
    success = len(errors_list) == 0

    return {
        "success": success,
        "image_paths": image_paths,
        "image_path": image_paths.get("front") if image_paths else None,
        "image_id": image_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processing_time_ms": processing_time_ms,
        "raw_ocr": raw_ocr,
        "detections": detections or [create_empty_detection(f) for f in MANDATORY_FIELDS],
        "readability": readability,
        "metadata": metadata or {},
        "errors": errors_list
    }


def validate_result_schema(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that an analysis result dictionary conforms to the schema (single or multi-image).

    Returns:
        (is_valid, list_of_validation_error_messages)
    """
    validation_errors = []

    required_common_keys = [
        "success", "image_id", "timestamp",
        "processing_time_ms", "raw_ocr", "detections",
        "readability", "metadata", "errors"
    ]

    for key in required_common_keys:
        if key not in result:
            validation_errors.append(f"Missing top-level key: '{key}'")

    if "image_path" not in result and "image_paths" not in result:
        validation_errors.append("Missing 'image_path' or 'image_paths' top-level key")

    if "detections" in result and isinstance(result["detections"], list):
        detection_keys = ["field", "label", "value", "raw_match", "confidence", "bbox", "source", "status"]
        for idx, det in enumerate(result["detections"]):
            if not isinstance(det, dict):
                validation_errors.append(f"Detection at index {idx} is not a dictionary")
                continue
            for d_key in detection_keys:
                if d_key not in det:
                    validation_errors.append(f"Detection at index {idx} missing '{d_key}'")
            if det.get("status") not in VALID_STATUSES:
                validation_errors.append(f"Invalid status '{det.get('status')}' in detection {det.get('field')}")
            if "source_image" in det and det["source_image"] is not None and not isinstance(det["source_image"], str):
                validation_errors.append(f"Invalid source_image '{det.get('source_image')}' in detection {det.get('field')}")

    return len(validation_errors) == 0, validation_errors

