"""
Image preprocessing module using OpenCV for the Legal Metrology AI Engine.
Prepares packaged commodity images for optimal OCR detection and recognition.
"""

import os
from typing import Tuple, List, Optional, Union
import cv2
import numpy as np

from config import (
    IMAGE_MIN_DIMENSION,
    IMAGE_MAX_DIMENSION,
    IMAGE_TARGET_SHORT_EDGE,
    SUPPORTED_EXTENSIONS
)


def validate_image_file(image_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that an image path exists, is non-empty, and has a supported format.

    Returns:
        (is_valid, error_message)
    """
    if not isinstance(image_path, str) or not image_path.strip():
        return False, "Image path must be a non-empty string"

    if not os.path.exists(image_path):
        return False, f"File does not exist: {image_path}"

    if not os.path.isfile(image_path):
        return False, f"Path is not a regular file: {image_path}"

    _, ext = os.path.splitext(image_path.lower())
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file extension '{ext}'. Supported: {sorted(list(SUPPORTED_EXTENSIONS))}"

    size_bytes = os.path.getsize(image_path)
    if size_bytes == 0:
        return False, f"Image file is empty (0 bytes): {image_path}"

    max_size_bytes = 20 * 1024 * 1024  # 20 MB
    if size_bytes > max_size_bytes:
        return False, f"Image file exceeds 20MB limit ({size_bytes / (1024*1024):.1f}MB): {image_path}"

    return True, None


def load_image(image_input: Union[str, np.ndarray]) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Load an image from a filepath or validate an existing numpy array.

    Returns:
        (image_bgr_array, error_message)
    """
    if isinstance(image_input, np.ndarray):
        if image_input.size == 0 or len(image_input.shape) < 2:
            return None, "Provided numpy array is empty or has invalid shape"
        return image_input.copy(), None

    is_valid, error_msg = validate_image_file(image_input)
    if not is_valid:
        return None, error_msg

    # Read image with OpenCV
    img = cv2.imread(image_input, cv2.IMREAD_COLOR)
    if img is None:
        return None, f"Failed to decode image file: {image_input}"

    return img, None


def resize_image(
    image: np.ndarray,
    min_dim: int = IMAGE_MIN_DIMENSION,
    max_dim: int = IMAGE_MAX_DIMENSION,
    target_short_edge: int = IMAGE_TARGET_SHORT_EDGE
) -> Tuple[np.ndarray, float]:
    """
    Conditionally resize an image if its dimensions fall outside acceptable bounds.
    Preserves aspect ratio.

    Returns:
        (resized_image, scale_factor)
        scale_factor = resized_dimension / original_dimension
        (e.g., scale_factor = 2.0 if upscaled, 0.5 if downscaled, 1.0 if unchanged)
    """
    h, w = image.shape[:2]
    shortest = min(h, w)
    longest = max(h, w)

    scale_factor = 1.0

    # Upscale if too small
    if shortest < min_dim:
        scale_factor = float(target_short_edge) / float(shortest)
    # Downscale if too large
    elif longest > max_dim:
        scale_factor = float(max_dim) / float(longest)

    if abs(scale_factor - 1.0) < 1e-3:
        return image, 1.0

    new_w = max(1, int(round(w * scale_factor)))
    new_h = max(1, int(round(h * scale_factor)))

    # Use INTER_CUBIC for upscaling (smoother text), INTER_AREA for downscaling
    interp = cv2.INTER_CUBIC if scale_factor > 1.0 else cv2.INTER_AREA
    resized = cv2.resize(image, (new_w, new_h), interpolation=interp)

    return resized, scale_factor


def apply_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert BGR image to single-channel grayscale if not already grayscale."""
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8)
) -> np.ndarray:
    """
    Apply Contrast-Limited Adaptive Histogram Equalization (CLAHE).
    Enhances local contrast on uneven lighting and shiny packaging.
    """
    gray = apply_grayscale(image)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return clahe.apply(gray)


def apply_denoise(image: np.ndarray, h: int = 10) -> np.ndarray:
    """
    Apply conservative Non-Local Means Denoising to reduce sensor noise
    without blurring critical fine characters.
    """
    gray = apply_grayscale(image)
    return cv2.fastNlMeansDenoising(gray, None, h=h, templateWindowSize=7, searchWindowSize=21)


def preprocess_image(
    image_input: Union[str, np.ndarray],
    enable_clahe: bool = True,
    enable_denoise: bool = False
) -> Tuple[Optional[np.ndarray], List[str], float, Optional[str]]:
    """
    Complete preprocessing pipeline for Legal Metrology commodity images.

    Args:
        image_input: Path to image or BGR numpy array.
        enable_clahe: Whether to apply CLAHE contrast enhancement (recommended: True).
        enable_denoise: Whether to apply denoising (recommended: False unless noisy).

    Returns:
        (processed_image, applied_steps_list, scale_factor, error_message)
    """
    img, error = load_image(image_input)
    if img is None:
        return None, [], 1.0, error

    applied_steps: List[str] = ["load"]

    # 1. Resize if dimensions are out of bounds
    img, scale_factor = resize_image(img)
    if abs(scale_factor - 1.0) >= 1e-3:
        applied_steps.append(f"resize(scale={scale_factor:.3f})")

    # 2. Grayscale conversion
    img = apply_grayscale(img)
    applied_steps.append("grayscale")

    # 3. CLAHE Contrast Enhancement
    if enable_clahe:
        img = apply_clahe(img)
        applied_steps.append("clahe")

    # 4. Optional Denoising
    if enable_denoise:
        img = apply_denoise(img)
        applied_steps.append("denoise")

    # 5. Convert back to 3-channel BGR representation for OCR pipeline compatibility
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    return img, applied_steps, scale_factor, None
