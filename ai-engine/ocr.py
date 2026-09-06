"""
OCR Wrapper module using PaddleOCR.
Abstracts PaddleOCR engine initialization and normalizes detection results.
Compatible with both PaddleOCR 3.x and 2.x return formats.
"""

from typing import List, Dict, Any, Union
import numpy as np
from paddleocr import PaddleOCR
from config import DEFAULT_OCR_MIN_CONFIDENCE

# Module-level cached OCR engine instance
_OCR_ENGINE = None


def get_ocr_engine() -> PaddleOCR:
    """
    Returns the cached PaddleOCR singleton engine instance.
    Downloads default English recognition and detection models on first call.
    """
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        _OCR_ENGINE = PaddleOCR()
    return _OCR_ENGINE


def run_ocr(
    image: Union[str, np.ndarray],
    min_confidence: float = DEFAULT_OCR_MIN_CONFIDENCE,
    scale_factor: float = 1.0
) -> List[Dict[str, Any]]:
    """
    Run PaddleOCR on an image path or numpy array.

    Args:
        image: Path to image or image numpy array.
        min_confidence: Minimum confidence to retain a detection.
        scale_factor: Scale factor applied during preprocessing (resized / original).
                      If != 1.0, bounding boxes are scaled back to original image dimensions.

    Returns:
        List of normalized detection dictionaries:
        [
            {
                "text": "Recognized Text",
                "confidence": 0.95,
                "bbox": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            },
            ...
        ]
        Results are sorted in reading-order (top-to-bottom, left-to-right).
    """
    engine = get_ocr_engine()

    # Call predict or ocr depending on available method
    if hasattr(engine, "predict"):
        raw_results = engine.predict(image)
    else:
        raw_results = engine.ocr(image)

    normalized_results: List[Dict[str, Any]] = []

    if not raw_results:
        return []

    # Inverse scale factor to map coordinates back to original image
    inv_scale = 1.0 / scale_factor if abs(scale_factor - 1.0) > 1e-3 and scale_factor > 0 else 1.0

    # Format A: PaddleOCR 3.x dict output: [{'rec_texts': [...], 'rec_scores': [...], 'rec_polys': [...]}]
    first_item = raw_results[0]
    if isinstance(first_item, dict) and "rec_texts" in first_item:
        rec_texts = first_item.get("rec_texts", [])
        rec_scores = first_item.get("rec_scores", [])
        rec_polys = first_item.get("rec_polys", [])

        for text, score, poly in zip(rec_texts, rec_scores, rec_polys):
            text = str(text).strip()
            confidence = float(score)
            if confidence < min_confidence or not text:
                continue

            # Convert poly to list of [x, y] coordinates scaled back to original dimensions
            if hasattr(poly, "tolist"):
                raw_poly = poly.tolist()
            else:
                raw_poly = poly

            bbox = [[round(float(p[0]) * inv_scale, 1), round(float(p[1]) * inv_scale, 1)] for p in raw_poly]

            normalized_results.append({
                "text": text,
                "confidence": round(confidence, 4),
                "bbox": bbox
            })

    # Format B: PaddleOCR 2.x classic list-of-lists output:
    # [ [ [bbox_4_points], (text, confidence) ], ... ]
    elif isinstance(first_item, list):
        for item in first_item:
            if not item or len(item) < 2:
                continue
            bbox_raw = item[0]
            text_info = item[1]
            if not text_info or len(text_info) < 2:
                continue

            text = str(text_info[0]).strip()
            confidence = float(text_info[1])
            if confidence < min_confidence or not text:
                continue

            bbox = [[round(float(point[0]) * inv_scale, 1), round(float(point[1]) * inv_scale, 1)] for point in bbox_raw]
            normalized_results.append({
                "text": text,
                "confidence": round(confidence, 4),
                "bbox": bbox
            })

    # Sort results in approximate reading order (top Y bucketed by 15px, then left X)
    normalized_results.sort(key=lambda r: (round(r["bbox"][0][1] / 15.0), r["bbox"][0][0]))

    return normalized_results
