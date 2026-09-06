"""
Readability and Font Height Estimation Module.
Provides lightweight pixel-based text-height indicators without claiming physical scale.
"""

from typing import List, Dict, Any, Tuple, Optional


DISCLAIMER_NOTE = (
    "Pixel-based estimate only. Cannot determine physical font size (mm) "
    "without camera calibration or reference scale. Not a legally authoritative measurement."
)


def estimate_readability(
    ocr_results: List[Dict[str, Any]],
    image_shape: Optional[Tuple[int, ...]] = None
) -> Dict[str, Any]:
    """
    Compute pixel-based readability indicators from OCR bounding boxes.

    Args:
        ocr_results: List of normalized OCR detection dicts with 'bbox' [[x,y],...]
        image_shape: (height, width, ...) from image.shape

    Returns:
        Dictionary adhering to the data contract readability schema:
        {
            "avg_text_height_px": float,
            "min_text_height_px": float,
            "max_text_height_px": float,
            "small_text_count": int,
            "image_resolution": [width, height],
            "estimated_readability": "good" | "moderate" | "poor",
            "note": str
        }
    """
    heights: List[float] = []

    for item in ocr_results:
        bbox = item.get("bbox")
        if bbox and len(bbox) == 4:
            y_coords = [pt[1] for pt in bbox]
            h = max(y_coords) - min(y_coords)
            if h > 0:
                heights.append(round(h, 1))

    if image_shape and len(image_shape) >= 2:
        img_h, img_w = image_shape[:2]
        resolution = [int(img_w), int(img_h)]
    else:
        resolution = [0, 0]

    if not heights:
        return {
            "avg_text_height_px": 0.0,
            "min_text_height_px": 0.0,
            "max_text_height_px": 0.0,
            "small_text_count": 0,
            "image_resolution": resolution,
            "estimated_readability": "poor",
            "note": DISCLAIMER_NOTE
        }

    min_h = min(heights)
    max_h = max(heights)
    avg_h = round(sum(heights) / len(heights), 1)
    small_text_count = sum(1 for h in heights if h < 14.0)

    # Heuristic readability rating
    if min_h >= 18.0 and (resolution[0] >= 800 or resolution[0] == 0):
        rating = "good"
    elif min_h >= 12.0:
        rating = "moderate"
    else:
        rating = "poor"

    return {
        "avg_text_height_px": avg_h,
        "min_text_height_px": min_h,
        "max_text_height_px": max_h,
        "small_text_count": small_text_count,
        "image_resolution": resolution,
        "estimated_readability": rating,
        "note": DISCLAIMER_NOTE
    }
