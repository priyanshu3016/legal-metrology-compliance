"""
Tests for image preprocessing module (preprocess.py)
"""

import os
import cv2
import numpy as np
import pytest

from preprocess import (
    validate_image_file,
    load_image,
    resize_image,
    apply_grayscale,
    apply_clahe,
    apply_denoise,
    preprocess_image
)

SAMPLE_IMAGE = "samples/compliant/sample_test_label.jpg"


def test_validate_image_file_valid():
    """Verify validation passes for an existing, valid image file."""
    assert os.path.exists(SAMPLE_IMAGE)
    is_valid, err = validate_image_file(SAMPLE_IMAGE)
    assert is_valid is True
    assert err is None


def test_validate_image_file_nonexistent():
    """Verify validation fails gracefully for a non-existent path."""
    is_valid, err = validate_image_file("samples/compliant/does_not_exist.jpg")
    assert is_valid is False
    assert "does not exist" in err


def test_validate_image_file_unsupported_ext():
    """Verify validation rejects unsupported extensions like .txt or .pdf."""
    tmp_path = "samples/test.txt"
    with open(tmp_path, "w") as f:
        f.write("dummy text")
    try:
        is_valid, err = validate_image_file(tmp_path)
        assert is_valid is False
        assert "Unsupported file extension" in err
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_load_image_valid():
    """Verify loading returns a valid BGR numpy array."""
    img, err = load_image(SAMPLE_IMAGE)
    assert err is None
    assert isinstance(img, np.ndarray)
    assert len(img.shape) == 3
    assert img.shape[2] == 3


def test_resize_small_image():
    """Verify small images (<640px) are upscaled with scale_factor > 1.0."""
    small = np.ones((200, 300, 3), dtype=np.uint8) * 255
    resized, scale = resize_image(small, min_dim=640, target_short_edge=1000)
    assert scale > 1.0
    assert min(resized.shape[:2]) >= 640


def test_resize_large_image():
    """Verify oversized images (>4000px) are downscaled with scale_factor < 1.0."""
    large = np.ones((4500, 5000, 3), dtype=np.uint8) * 255
    resized, scale = resize_image(large, max_dim=4000)
    assert scale < 1.0
    assert max(resized.shape[:2]) <= 4000


def test_resize_normal_image_unchanged():
    """Verify normal dimension images remain unchanged with scale_factor == 1.0."""
    normal = np.ones((800, 1200, 3), dtype=np.uint8) * 255
    resized, scale = resize_image(normal, min_dim=640, max_dim=4000)
    assert scale == 1.0
    assert resized.shape == normal.shape


def test_grayscale():
    """Verify grayscale converts 3-channel to 1-channel 2D array."""
    color = np.ones((100, 100, 3), dtype=np.uint8) * 255
    gray = apply_grayscale(color)
    assert len(gray.shape) == 2


def test_clahe():
    """Verify CLAHE processes grayscale input and returns same dimensions."""
    gray = np.linspace(0, 255, 10000, dtype=np.uint8).reshape((100, 100))
    clahe_res = apply_clahe(gray)
    assert clahe_res.shape == gray.shape


def test_denoise():
    """Verify denoising operates without crashing and preserves shape."""
    noisy = (np.ones((100, 100), dtype=np.uint8) * 128)
    denoised = apply_denoise(noisy, h=5)
    assert denoised.shape == noisy.shape


def test_full_preprocessing_pipeline():
    """Verify complete preprocessing pipeline end-to-end on sample image."""
    img, steps, scale, err = preprocess_image(SAMPLE_IMAGE, enable_clahe=True, enable_denoise=True)
    assert err is None
    assert img is not None
    assert isinstance(steps, list)
    assert "grayscale" in steps
    assert "clahe" in steps
    assert "denoise" in steps
    assert isinstance(scale, float)
    assert len(img.shape) == 3 and img.shape[2] == 3
