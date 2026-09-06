# AI Engine — Legal Metrology Compliance OCR & Declaration Extraction

> **Smart India Hackathon 2026 — Problem Statement 26034**  
> **Component:** AI Engine (Person 5)  
> **Consumers:** Backend (Person 3), Rules Engine (Person 6), Frontend Evidence Viewer (Persons 1 & 2)

---

## 1. Overview & Architecture

The AI Engine processes commodity package images locally using OpenCV and PaddleOCR to identify mandatory declarations under the **Legal Metrology (Packaged Commodities) Rules, 2011**:

1. **Product Name** (`product_name`)
2. **Manufacturer / Packer / Importer** (`manufacturer_packer_importer`)
3. **Net Quantity** (`net_quantity`)
4. **Maximum Retail Price** (`mrp`)
5. **Manufacturing / Packing Date** (`manufacturing_date`)
6. **Consumer Care Details** (`consumer_care`)
7. **Country of Origin** (`country_of_origin`)
8. **Best Before / Use By** (`best_before`)
9. **Unit Sale Price** (`unit_sale_price`)

---

## 2. Integration Guide for Person 3 (Backend / FastAPI)

### Function Signature
```python
def analyze_image(image_path: str, demo_mode: bool = False) -> dict
```

- **image_path** *(str)*: Absolute or relative filepath to the image on disk.
- **demo_mode** *(bool)*: Optional. Set to `True` during rehearsals or controlled presentation pitch to load verified fallback data.
- **Returns** *(dict)*: Structured JSON contract (guaranteed never to raise unhandled exceptions).

### FastAPI Route Integration Example
```python
import os
import sys
from fastapi import FastAPI, UploadFile, File
import shutil

# Ensure ai-engine is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-engine")))
from analyzer import analyze_image

app = FastAPI(title="Legal Metrology Compliance API")

@app.post("/api/v1/inspect")
async def inspect_commodity_label(file: UploadFile = File(...), demo: bool = False):
    upload_dir = "/tmp/compliance_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, file.filename)

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Run AI OCR + Extraction Pipeline
        result = analyze_image(temp_path, demo_mode=demo)
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

---

## 3. Integration Guide for Person 6 (Rules Engine)

The AI Engine extracts and normalizes values, but **never** makes legal compliance decisions.
Person 6 inspects the `detections` list in the returned JSON:

```json
{
  "field": "mrp",
  "label": "Maximum Retail Price",
  "value": "20.00",
  "raw_match": "MRP Rs. 20.00 (incl. of all taxes)",
  "confidence": 0.9827,
  "bbox": [[0.0, 151.6], [539.2, 150.4], [539.2, 192.8], [0.0, 194.0]],
  "source": "ocr",
  "status": "found"
}
```

### Detection Statuses
- `"found"`: Field extracted with high confidence ($\ge 0.60$).
- `"low_confidence"`: Field extracted with confidence $< 0.60$.
- `"not_found"`: Mandatory field missing from OCR text (`value` and `bbox` are `null`).

### Bounding Box Polygon Format
Each bounding box is a 4-point list `[[x1, y1], [x2, y2], [x3, y3], [x4, y4]]` mapped to the original image dimensions, allowing Frontend (Persons 1 & 2) to render highlight overlays directly on the uploaded image.

---

## 4. Running the CLI & Automated Tests

### Virtual Environment Setup
```bash
cd ai-engine
source venv/bin/activate
```

### Run CLI on an Image
```bash
# Single image mode
python analyze.py samples/compliant/sample_test_label.jpg

# Multi-image mode
python analyze.py --front samples/compliant/demo_product_01_front.jpg --back samples/compliant/demo_product_01_back.jpg --side samples/compliant/demo_product_01_side.jpg
```

### Run Full Test Suite
```bash
python -m pytest tests/ -v
```

---

## 5. Multi-Image Inspection Extension

The AI Engine supports multi-image package inspections (front, back, and optional side views) of the same commodity package. The engine processes views independently, tracks declarations back to their source views, and merges fields cleanly.

### Function Signature
```python
def analyze_multi_image(
    front_image_path: str,
    back_image_path: str,
    side_image_path: Optional[str] = None,
    demo_mode: bool = False
) -> dict
```

- **front_image_path** *(str)*: Required path to the front label image.
- **back_image_path** *(str)*: Required path to the back label image.
- **side_image_path** *(str, optional)*: Optional path to side panel image (`None` if omitted).
- **demo_mode** *(bool)*: Optional. Fast pre-verified fallback for demonstration sets.
- **Returns** *(dict)*: Multi-image AnalysisResult JSON conforming to the contract.

### Key Output Schema Extensions
1. **`image_paths`**: Dict containing paths for `{"front": "...", "back": "...", "side": ...}`.
2. **`source_image`**: Set on each detection dict indicating whether the declaration was discovered on `"front"`, `"back"`, or `"side"`.
3. **`status: "ambiguous"`**: When contradictory values appear across multiple views (e.g. MRP 120 on front vs 110 on back), the status is set to `"ambiguous"`, the highest-confidence item is primary, and all options are presented in a `"candidates"` array:
   ```json
   {
     "field": "mrp",
     "value": "120.00",
     "confidence": 0.94,
     "source_image": "front",
     "status": "ambiguous",
     "candidates": [
       {"value": "120.00", "confidence": 0.94, "source_image": "front", "bbox": [...]},
       {"value": "110.00", "confidence": 0.91, "source_image": "back", "bbox": [...]}
     ]
   }
   ```
4. **Per-Image Readability & Raw OCR**: `readability` and `raw_ocr` are structured per view (`front`, `back`, `side`) so pixel measurements are never mixed across different images.

### Backend Integration Example (Person 3)
```python
@app.post("/api/v1/inspect-multi")
async def inspect_multi_endpoint(
    front: UploadFile = File(...),
    back: UploadFile = File(...),
    side: Optional[UploadFile] = File(None),
    demo: bool = False
):
    upload_dir = "/tmp/compliance_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    front_path = os.path.join(upload_dir, front.filename)
    back_path = os.path.join(upload_dir, back.filename)
    side_path = os.path.join(upload_dir, side.filename) if side else None

    # Save uploads to disk
    with open(front_path, "wb") as f:
        shutil.copyfileobj(front.file, f)
    with open(back_path, "wb") as f:
        shutil.copyfileobj(back.file, f)
    if side and side_path:
        with open(side_path, "wb") as f:
            shutil.copyfileobj(side.file, f)

    try:
        result = await asyncio.to_thread(
            analyze_multi_image,
            front_image_path=front_path,
            back_image_path=back_path,
            side_image_path=side_path,
            demo_mode=demo
        )
        return result
    finally:
        for path in [front_path, back_path, side_path]:
            if path and os.path.exists(path):
                os.remove(path)
```

