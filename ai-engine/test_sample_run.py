"""
Helper script to generate a sample test label for Phase 1 verification.
"""

import cv2
import numpy as np
from ocr import run_ocr

def create_sample_label():
    # Create white canvas
    img = np.ones((400, 700, 3), dtype=np.uint8) * 255

    # Draw simulated label text
    lines = [
        ("Parle-G Gold Biscuits", (30, 60), 1.0, (0, 0, 0), 2),
        ("Net Wt: 100g", (30, 120), 0.9, (0, 0, 0), 2),
        ("MRP Rs. 20.00 (incl. of all taxes)", (30, 180), 0.9, (0, 0, 0), 2),
        ("Mfg Date: 03/2026", (30, 240), 0.9, (0, 0, 0), 2),
        ("Country of Origin: India", (30, 300), 0.9, (0, 0, 0), 2),
        ("Customer Care: 1800-22-2211", (30, 350), 0.8, (0, 0, 0), 2)
    ]

    for text, origin, scale, color, thickness in lines:
        cv2.putText(img, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)

    sample_path = "samples/compliant/sample_test_label.jpg"
    cv2.imwrite(sample_path, img)
    print(f"Generated synthetic test image: {sample_path}")
    return sample_path

if __name__ == "__main__":
    path = create_sample_label()
    print("Running OCR inference...")
    results = run_ocr(path)
    print(f"\n--- Extracted {len(results)} OCR lines ---")
    for r in results:
        print(f"Text: '{r['text']}' | Confidence: {r['confidence']:.2f} | BBox: {r['bbox'][0]}")
