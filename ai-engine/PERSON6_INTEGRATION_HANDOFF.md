# Person 6 Integration Handoff — AI/OCR Engine to Compliance Rules Engine

> **Document Version:** 1.0.0  
> **Date:** September 5, 2026  
> **Author:** Person 5 (AI / OCR / Field Extraction Module Lead)  
> **Audience:** Person 6 (Legal Metrology Compliance & Rules Engine Lead), Person 3/4 (FastAPI Backend / Integration)  
> **Scope:** Complete specification of the implemented AI engine, input/output data contracts, field semantics, multi-image merging, edge cases, and legal responsibility boundaries.

---

## 1. Overview

This document defines the integration boundary between the **AI/OCR Engine** (owned by Person 5) and the **Legal Metrology Compliance Rules Engine** (owned by Person 6) for Smart India Hackathon 2026 (Problem Statement 26034).

### The Core Architectural Principle
- **Person 5 (AI Engine)** answers: *"What text and values are physically visible and detectable on these package images?"*
- **Person 6 (Rules Engine)** answers: *"Given what was detected, is this packaged commodity legally compliant with the Legal Metrology (Packaged Commodities) Rules, 2011?"*

**Person 5 never issues legal judgments (PASS, FAIL, WARNING, violation penalty, exemption).**  
A status of `"not_found"` from Person 5 simply means the AI did not extract a declaration; it is Person 6's responsibility to decide whether that absence constitutes a violation, a warning, or a legal exemption under the rules.

---

## 2. Architecture & Pipeline Flow

The AI Engine is an in-process Python package invoked directly by the FastAPI backend (Person 3). It is **not** an external HTTP microservice and requires **no cloud OCR** or external API calls.

```
[ Front Image ]  (Required)
[ Back Image  ]  (Required)
[ Side Image  ]  (Optional)
       │
       ▼
1. Validation & Loading (`preprocess.py`)
       │
       ▼
2. Contrast Enhancement & Resize (`preprocess.py` - CLAHE + aspect-preserving scale)
       │
       ▼
3. Local OCR Inference (`ocr.py` - PaddleOCR 3.x / PP-OCRv6)
       │ (Coordinate remapping to original pixel space via inverse scale factor)
       ▼
4. Per-Image 9-Field Extraction (`extractor.py` - Regex + heuristics)
       │
       ▼
5. Multi-Image Canonical Merge (`extractor.py::merge_detections()`)
       │
       ▼
6. Readability & Text Height Estimation (`readability.py` - per-image pixel stats)
       │
       ▼
7. Unified Analysis Result JSON (`schemas.py::create_multi_analysis_result()`)
       │
       ▼
[ Person 6: Legal Metrology Compliance Engine ]
       │
       ▼
Final Inspection Result: PASS / FAIL / WARNING / Violations / Score
```

---

## 3. Public AI API

The single module entry point for Person 3 and Person 6 is [`analyzer.py`](file:///Users/priyanshu/legal-metrology-compliance/ai-engine/analyzer.py).

### 3.1 Primary Function: `analyze_multi_image`

```python
from analyzer import analyze_multi_image

result: dict = analyze_multi_image(
    front_image_path: str,
    back_image_path: str,
    side_image_path: Optional[str] = None,
    demo_mode: bool = False
)
```

#### Arguments
| Argument | Type | Required | Default | Description |
|---|---|---|---|---|
| `front_image_path` | `str` | **Yes** | — | Absolute or relative filesystem path to the front packaging image. |
| `back_image_path` | `str` | **Yes** | — | Absolute or relative filesystem path to the back packaging image. |
| `side_image_path` | `Optional[str]` | No | `None` | Path to side flap / view. If `None` or corrupt, processing proceeds without failure. |
| `demo_mode` | `bool` | No | `False` | When `True`, checks if inputs match pre-verified pitch demo samples. **Must be `False` in production.** |

#### Exception Safety
`analyze_multi_image()` **never raises uncaught exceptions**. All runtime exceptions are caught internally and returned as structured errors inside `result["errors"]` with `result["success"] = False`.

### 3.2 Legacy Single-Image Function: `analyze_image`

```python
from analyzer import analyze_image

result: dict = analyze_image(
    image_path: str,
    demo_mode: bool = False
)
```
Maintained for backward compatibility and single-label testing. Runs the identical 9-field extraction pipeline on one image.

---

## 4. Input Contract

### 4.1 Supported File Types
- Extensions: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`
- Color space: BGR / RGB (loaded via OpenCV `cv2.imread`)
- File size: Up to 20 MB per image
- Resolution: Automatically resized if short edge < 640px or long edge > 4000px. Bounding box coordinates in output are automatically mapped back to original image coordinates.

### 4.2 Handling of Missing / Corrupt Views
- **Missing Front Image**: Returns immediately with `success: false` and `errors: [{"code": "MISSING_FRONT_IMAGE", ...}]`.
- **Missing Back Image**: Returns immediately with `success: false` and `errors: [{"code": "MISSING_BACK_IMAGE", ...}]`.
- **Absent Side Image (`None`)**: Handled gracefully. `metadata["images_supplied"]` contains `["front", "back"]`, `raw_ocr["side"]` is `None`, and `readability["side"]` is `None`.
- **Invalid Side Image (path provided but corrupt/missing file)**: Processing does **not** abort. An error with code `"SIDE_IMAGE_INVALID"` is appended to `errors[]`, and inspection completes using front and back views.

---

## 5. Output Contract

The return value of `analyze_multi_image()` is a Python `dict` conforming to the schema below.

### 5.1 Top-Level Schema

```json
{
  "success": true,
  "image_paths": {
    "front": "samples/1.jpg",
    "back": "samples/2.jpg",
    "side": null
  },
  "image_path": "samples/1.jpg",
  "image_id": "1",
  "timestamp": "2026-09-05T16:26:06.123456+00:00",
  "processing_time_ms": 1420,
  "raw_ocr": {
    "front": { "full_text": "...", "line_count": 9, "avg_confidence": 0.985, "ocr_results": [...] },
    "back": { "full_text": "...", "line_count": 32, "avg_confidence": 0.962, "ocr_results": [...] },
    "side": null
  },
  "detections": [ /* Exactly 9 objects, one per mandatory declaration */ ],
  "readability": {
    "front": { "avg_text_height_px": 178.7, "min_text_height_px": 54.0, "max_text_height_px": 518.0, "small_text_count": 0, "image_resolution": [2086, 2581], "estimated_readability": "good", "note": "..." },
    "back": { "avg_text_height_px": 88.8, "min_text_height_px": 29.0, "max_text_height_px": 179.0, "small_text_count": 0, "image_resolution": [2371, 3567], "estimated_readability": "good", "note": "..." },
    "side": null
  },
  "metadata": {
    "ocr_engine": "paddleocr",
    "images_supplied": ["front", "back"],
    "images_absent": ["side"],
    "preprocessing_applied": {
      "front": ["load", "grayscale", "clahe"],
      "back": ["load", "grayscale", "clahe"]
    },
    "demo_mode": false
  },
  "errors": []
}
```

### 5.2 Top-Level Field Descriptions
| Key | Type | Description | Person 6 Relevance |
|---|---|---|---|
| `success` | `bool` | `True` if pipeline ran without fatal input validation errors. | **Consume**: If `False`, abort rules evaluation. |
| `image_paths` | `dict` | Mapping of `{"front": path, "back": path, "side": path\|null}`. | Reference for audits. |
| `image_path` | `str` | Preserved for backward compatibility (mirrors front path). | Ignore. |
| `image_id` | `str\|null` | Filename slug without extension. | Reference for logging. |
| `timestamp` | `str` | ISO-8601 UTC timestamp of inspection execution. | Reference for records. |
| `processing_time_ms` | `int` | Execution duration in milliseconds. | Informational / performance telemetry. |
| `raw_ocr` | `dict` | Per-image dictionary containing raw OCR text and bounding boxes. | Secondary evidence / debugging. |
| `detections` | `list` | Canonical list of 9 mandatory declaration field objects. | **PRIMARY INPUT FOR PERSON 6**. |
| `readability` | `dict` | Per-image pixel text height metrics and qualitative ratings. | Informational only (do not use for legal font size). |
| `metadata` | `dict` | Engine parameters, supplied/absent views, preprocessing steps. | Verification & context. |
| `errors` | `list` | List of non-fatal and fatal error objects `[{"code": str, "message": str}]`. | **Consume**: Flag system warnings or failure reasons. |

---

## 6. Detection Schema (`detections[]`)

`result["detections"]` always contains **exactly 9 items**, representing the 9 mandatory declarations under the Legal Metrology (Packaged Commodities) Rules, 2011.

```json
{
  "field": "net_quantity",
  "label": "Net Quantity",
  "value": "30.5 g",
  "raw_match": "30.5 g (28 g+2.5 g)",
  "confidence": 0.8978,
  "bbox": [
    [866.0, 3426.0],
    [1225.0, 3431.0],
    [1223.0, 3549.0],
    [865.0, 3544.0]
  ],
  "source": "ocr",
  "source_image": "back",
  "status": "found"
}
```

### 6.1 Detection Object Keys
| Field | Type | Description |
|---|---|---|
| `field` | `str` | Canonical machine-readable field identifier (see Section 8). |
| `label` | `str` | Human-readable English label for display. |
| `value` | `str \| null` | Extracted and normalized declaration value. `null` if not found. |
| `raw_match` | `str \| null` | Unprocessed OCR line or line segment where detection occurred. |
| `confidence` | `float` | OCR confidence between `0.0` and `1.0` (`0.0` if not found). |
| `bbox` | `list \| null` | 4-point polygon `[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]` in original image coordinates. |
| `source` | `str` | Data provenance: `"ocr"` or `"demo_fallback"`. |
| `source_image` | `str \| null` | Packaging view where the winning declaration was located: `"front"`, `"back"`, `"side"`, or `null`. |
| `status` | `str` | Extraction outcome: `"found"`, `"low_confidence"`, `"not_found"`, or `"ambiguous"`. |
| `candidates` | `list \| null` | **Only present when `status == "ambiguous"`**. Contains conflicting candidate detections from different views. |

### 6.2 Status Values & Exact Meanings
| Status String | Meaning for AI Engine | Meaning for Person 6 Rules Engine |
|---|---|---|
| `"found"` | The field was confidently detected (`confidence >= 0.60`) and verified by heuristic regex/validation. | Evaluate `value` against Legal Metrology rules (units, formats, dates). |
| `"low_confidence"` | Text matching the field pattern was detected, but OCR confidence was below threshold (`< 0.60`). | Flag for human reviewer or trigger a soft compliance WARNING. |
| `"not_found"` | No valid declaration candidate was detected in any supplied view. `value` is `null`, `confidence` is `0.0`. | **Check legal requirements**: Is this declaration mandatory for this product category, or is there a statutory exemption? Issue FAIL or EXEMPTION accordingly. |
| `"ambiguous"` | Different packaging views yielded conflicting values (e.g. front: "Brand A", back: "Brand B"). `value` holds the highest-confidence candidate. | Check `candidates[]`. Flag as ambiguous or evaluate both candidates against rules. |

---

## 7. Multi-Image Merge Behavior

Detections from individual image views are merged into the final 9 fields by [`extractor.py::merge_detections()`](file:///Users/priyanshu/legal-metrology-compliance/ai-engine/extractor.py).

### Merge Algorithm Rules
1. **Field Only in One View**: If a field is found on only one image (e.g., `product_name` on front, or `consumer_care` on back), that detection is used directly. Its `status` is preserved (`"found"` or `"low_confidence"`), and `source_image` indicates the originating view.
2. **Field in Multiple Views with Consistent Values**: If multiple views detect the same field with equivalent values (compared case-insensitively, or numerically for prices):
   - The detection with the **highest confidence** is selected.
   - Its `status` is `"found"`.
   - Its `source_image` indicates where the highest-confidence detection was found.
3. **Field in Multiple Views with Conflicting Values**: If two views detect different values (e.g., front candidate = "Amul", back candidate = "Parle"):
   - Primary `value` is set to the highest-confidence candidate.
   - `status` is set to `"ambiguous"`.
   - A `candidates` list is added to the detection object, documenting all competing candidates:
     ```json
     "candidates": [
       { "value": "Value A", "confidence": 0.98, "source_image": "front", "bbox": [...] },
       { "value": "Value B", "confidence": 0.91, "source_image": "back", "bbox": [...] }
     ]
     ```
4. **Field Absent Across All Views**: An empty detection object is returned with `status: "not_found"`, `value: null`, `confidence: 0.0`, `bbox: null`, `source_image: null`.

**Crucial Note:** Merging performs string and numeric comparison only. It does **not** attempt legal reconciliation.

---

## 8. Field-by-Field Semantics

Below is the complete dictionary of all 9 fields extracted by the AI Engine.

| Field Name (`field`) | Label (`label`) | Extracted Format / Example | Extraction Logic Summary |
|---|---|---|---|
| `product_name` | Product Name | `"Amul"`, `"Parle-G Gold Biscuits"` | Visual prominence heuristic (bounding box height, top placement on packaging). Rejects code tokens (`BN:`, `KAF2151`), dates, URLs, addresses, consonant clusters (`MDD`), and marketing/flavor descriptors (`"MAGIC MASALA"`, `"FINEST POTATOES"`). Returns `null` if brand not detected. |
| `manufacturer_packer_importer` | Manufacturer / Packer / Importer | `"Kaira District Co-operative Milk Producers'Union Ltd., Anand-388 001, India."` | Recognizes entity lines prefixed with `Manufactured by:`, `Packed by:`, `Marketed by:` or standalone company indicators (`Ltd.`, `Pvt. Ltd.`, `Co-operative`) paired with postal PIN codes or address lines. Does **not** fabricate names from truncated fragments (`"Mfg. & Mk"`). |
| `net_quantity` | Net Quantity | `"200 g"`, `"1.5 l"`, `"30.5 g"` | Recognizes standard prefixes (`Net Wt:`, `Net Qty:`, `Weight:`) and promotional pack formats (`"30.5 g (28 g+2.5 g)"`). Normalizes units (`gms` $\rightarrow$ `g`, `mL` $\rightarrow$ `ml`, `ltr` $\rightarrow$ `l`). Strictly excludes nutrition panel lines (`6.6g`, `33 g`, `14.9 g`). |
| `mrp` | Maximum Retail Price | `"10"`, `"120.00"` | Recognizes `MRP Rs. 10/-`, `M.R.P. ₹ 120.00`, `MRP: 250`. Extracts numeric string only (without currency symbols). Returns `null` if only disclaimer text is present without a price number. |
| `manufacturing_date` | Manufacturing / Packing Date | `"03/AUG/26"`, `"03/2026"`, `"25/08/26"` | Recognizes `Mfg Date:`, `Mfd:`, `Packed:`, `PKD:`, and joint declarations (`"MFD & USE BY: 25/08/26 & 07/01/27"` $\rightarrow$ date1). Disqualifies prose disclaimers (`"see below"`). |
| `consumer_care` | Consumer Care Details | `"1800 2583333 \| customercare@amul.coop"` | Extracts toll-free phone numbers (`1800...`, `+91...`) and support email addresses. Combines them with pipe separator (`\|`). Rejects prose lines without contact numbers/emails. |
| `country_of_origin` | Country of Origin | `"India"`, `"Germany"` | Recognizes explicit statements: `Country of Origin: India`, `Made in Germany`. **Never infers country of origin merely because "India" appears in a manufacturer address.** |
| `best_before` | Best Before / Use By | `"03/AUG/27"`, `"07/01/27"`, `"6 months from manufacture"` | Recognizes duration expressions (`"Best Before 12 months"`, `"Shelf Life 6 months"`), calendar dates (`"EXP:03/AUG/27"`), and joint declarations (`"MFD & USE BY:"` $\rightarrow$ date2). Rejects generic disclaimers lacking a date (`"EXPIRY DATE, WHICHEVER IS EARLIER."`). |
| `unit_sale_price` | Unit Sale Price | `"₹0.65 / g"`, `"₹0.33 / g"`, `"₹10 / 100g"` | Recognizes `Unit Sale Price: ₹... per ...`, `USP 0.65/g`, and standalone `Rs. 0.33/- PER g`. Requires recognized units (`g`, `kg`, `ml`, `l`, `pcs`, `100g`). Narrowly corrects `/9` to `/g` only in immediate price slash context (`USP 0.65/9`). |

---

## 9. Confidence, Bounding Box, and Source Semantics

### 9.1 Confidence Score (`confidence`)
- Value range: `0.0` to `1.0`.
- Represents the **OCR engine's character recognition probability** for the matched text.
- `confidence >= 0.60`: Yields `status: "found"`.
- `0.0 < confidence < 0.60`: Yields `status: "low_confidence"`.
- `confidence == 0.0`: Field was not detected (`status: "not_found"`).
- **Important:** OCR confidence measures visual legibility, **not semantic or legal correctness**. A high confidence score (e.g. `0.999`) means the text was cleanly read, not that the manufacturer complied with law.

### 9.2 Bounding Box (`bbox`)
- Format: Standard 4-point polygon `[[x1, y1], [x2, y2], [x3, y3], [x4, y4]]` representing top-left, top-right, bottom-right, bottom-left coordinates.
- **Coordinate Space:** Mapped directly to the **original unscaled input image dimensions in pixels**.
- When a detection spans multiple lines (e.g. manufacturer name + address, or phone + email), `bbox` is the bounding box union enclosing all constituent text lines.
- `bbox == null`: When `status: "not_found"`.

### 9.3 Source Image (`source_image`)
- Identifies which physical view provided the detection:
  - `"front"`: Extracted from `front_image_path`.
  - `"back"`: Extracted from `back_image_path`.
  - `"side"`: Extracted from `side_image_path`.
  - `null`: Field not found in any view.

---

## 10. Readability Output

The AI Engine computes pixel-based text height indicators via [`readability.py`](file:///Users/priyanshu/legal-metrology-compliance/ai-engine/readability.py) for each view independently.

```json
"readability": {
  "back": {
    "avg_text_height_px": 88.8,
    "min_text_height_px": 29.0,
    "max_text_height_px": 179.0,
    "small_text_count": 0,
    "image_resolution": [2371, 3567],
    "estimated_readability": "good",
    "note": "Pixel-based estimate only. Cannot determine physical font size (mm) without camera calibration or reference scale. Not a legally authoritative measurement."
  }
}
```

### Critical Legal Limitation for Person 6
> [!WARNING]  
> **Do NOT use `readability` for Legal Metrology Rule 9 font-size compliance.**  
> Rule 9 specifies font height in **physical millimeters** (e.g. minimum 1.0mm, 2.0mm, or 4.0mm depending on package net quantity and area of principal display panel).  
> The AI engine cannot convert image pixels to real-world millimeters without a calibrated reference scale (such as a ruler or ArUco marker in the frame) and camera optical parameters.  
> `estimated_readability` (`"good"` / `"moderate"` / `"poor"`) is a pixel clarity heuristic for UI warning indicators only.

---

## 11. Errors and Edge Cases

Errors are returned in the top-level `errors` list as structured objects: `{"code": str, "message": str}`.

### Standard Error Codes
| Code | Condition | Severity |
|---|---|---|
| `MISSING_FRONT_IMAGE` | Front image path was empty or not provided. | Fatal (`success: false`) |
| `MISSING_BACK_IMAGE` | Back image path was empty or not provided. | Fatal (`success: false`) |
| `IMAGE_NOT_FOUND` | Specified image file does not exist on disk. | Fatal (`success: false`) |
| `UNSUPPORTED_FORMAT` | File extension is not in supported set (`.jpg`, `.png`, etc.) or file exceeds 20MB. | Fatal (`success: false`) |
| `IMAGE_UNREADABLE` | File could not be decoded as an image by OpenCV. | Fatal (`success: false`) |
| `PREPROCESSING_FAILED` | Internal error during image scaling or filtering. | Fatal (`success: false`) |
| `OCR_FAILED` | PaddleOCR execution crashed on single image. | Fatal (`success: false`) |
| `MULTI_ANALYSIS_FAILED` | Unhandled exception during multi-image orchestration. | Fatal (`success: false`) |
| `SIDE_IMAGE_INVALID` | Side image path was provided but file was missing/corrupt. | **Non-fatal** (`success: true`, side image skipped) |

---

## 12. Demo Mode

- **What it is:** A hardcoded fallback dataset ([`demo_fallback.py`](file:///Users/priyanshu/legal-metrology-compliance/ai-engine/demo_fallback.py)) designed for Smart India Hackathon stage presentations to guard against poor conference Wi-Fi, extreme glare, or projector failure.
- **How it works:** Activated by setting `demo_mode=True`. If the input filenames match known demo samples (e.g. `demo_product_01_front.jpg`), it returns pre-verified ground truth data.
- **Person 6 Recommendation:** **Always keep `demo_mode=False`** when evaluating compliance rules in production or real-world audits to ensure all decisions are based strictly on live OCR detections.

---

## 13. Real Product Validation Results

The pipeline has been verified on live consumer packaging samples:

### Sample 1: Amul Butter (`samples/1.jpg` [front] + `samples/2.png` [back])
| Field | Result Value | Status | Source | Behavior Notes |
|---|---|---|---|---|
| `product_name` | `"Amul"` | `found` | `front` | Selected based on visual prominence (329.7px height). Noise code `:KAF2151` and `MDD` on back were cleanly rejected. |
| `manufacturer_packer_importer` | `"Kaira District Co-operative Milk Producers'Union Ltd., Anand-388 001, India."` | `found` | `back` | Extracted from `Manufactured by:` line with address continuation. |
| `net_quantity` | `"200 g"` | `found` | `back` | Extracted from `NetWeight: 200g`. Standardized unit. |
| `mrp` | `null` | `not_found` | `null` | Stamped MRP was not captured in OCR frame. Correctly returns `not_found` without hallucinating a number. |
| `manufacturing_date` | `"03/AUG/26"` | `found` | `back` | Extracted from `PKD:03/AUG/26`. |
| `consumer_care` | `"1800 2583333 \| customercare@amul.coop"` | `found` | `back` | Extracted toll-free number and email address; prose discarded. |
| `country_of_origin` | `null` | `not_found` | `null` | Not falsely inferred from "India" inside manufacturer address. |
| `best_before` | `"03/AUG/27"` | `found` | `back` | Extracted from line `T30 USP 0.65/9 EXP:03/AUG/27`. |
| `unit_sale_price` | `"₹0.65 / g"` | `found` | `back` | Narrow `/9` $\rightarrow$ `/g` correction applied in USP slash context. |

### Sample 2: Lay's Potato Chips (`samples/1.jpg` [front] + `samples/2.jpg` [back])
| Field | Result Value | Status | Source | Behavior Notes |
|---|---|---|---|---|
| `product_name` | `null` | `not_found` | `null` | OCR missed the ribbon logo `"Lay's"`. Flavor descriptor `"MAGIC MASALA"` was rejected. Accurately returns `not_found` rather than guessing. |
| `manufacturer_packer_importer` | `null` | `not_found` | `null` | OCR captured only `"Mfg. & Mk"`. Incomplete fragment rejected; no company name fabricated. |
| `net_quantity` | `"30.5 g"` | `found` | `back` | Extracted from promotional pack declaration `"30.5 g (28 g+2.5 g)"`. Nutrition table numbers avoided. |
| `mrp` | `"10"` | `found` | `back` | Extracted from `"MRP Rs. 10/- (INCL. OF ALL TAXES)"`. |
| `manufacturing_date` | `"25/08/26"` | `found` | `back` | Extracted date1 from joint declaration `"MFD & USE BY:"` + `"25/08/26 & 07/01/27"`. |
| `consumer_care` | `"1800 22 4020 \| CONSUMER.FEEDBACK@PEPSICO.COM"` | `found` | `back` | Extracted phone and email. |
| `country_of_origin` | `null` | `not_found` | `null` | Absent on packaging. |
| `best_before` | `"07/01/27"` | `found` | `back` | Extracted date2 from joint declaration. |
| `unit_sale_price` | `"₹0.33 / g"` | `found` | `back` | Extracted from `"Rs. 0.33/- PER g"`. |

---

## 14. Current Limitations

1. **Stylized / Logo-Only Brand Names**: Brand names embedded in graphic logos (such as the curved Lay's banner ribbon) may not be detected by generic OCR models. The engine prefers returning `not_found` over returning flavor text.
2. **Inkjet Stamped Flaps**: Dot-matrix inkjet stamping for batch numbers, MRP, and dates on shiny foil flaps can suffer from low OCR contrast. If the MRP number is missing from the image frame, it remains `not_found`.
3. **No Metric Font Measurement**: Physical font dimensions (mm) cannot be calculated without hardware calibration.
4. **Domestic Country of Origin**: Many Indian domestic products omit an explicit "Country of Origin: India" line and rely on the manufacturer's Indian address. The AI will report `country_of_origin: not_found` because the explicit declaration is absent. Person 6's rules engine must apply the Legal Metrology rule regarding domestic manufacturer address sufficiency.

---

## 15. Integration Contract for Person 6

### Data Ingestion Mapping

```
AI Engine result["detections"]
       │
       ▼
Person 6 Compliance Engine Loop:
for item in result["detections"]:
    field  = item["field"]        # Which mandatory declaration?
    status = item["status"]       # found | low_confidence | not_found | ambiguous
    value  = item["value"]        # Cleaned string or None
    source = item["source_image"] # front | back | side | None
```

### Recommendation Matrix for Person 6
| AI Detection Status | Recommended Legal Metrology Rule Decision |
|---|---|
| `status: "found"` | **Validate Value Content**: Check unit legality (e.g. grams vs non-standard units), date format validity, MRP format, presence of consumer care contacts. If valid $\rightarrow$ **PASS**. If invalid $\rightarrow$ **FAIL / WARNING**. |
| `status: "low_confidence"` | **Legibility Warning**: Declaration is present but poorly printed or blurry. Flag as **WARNING** (Potential legibility violation under Rule 9) or request manual verification. |
| `status: "not_found"` | **Check Exemption / Requirement**: Is this field required for this commodity? E.g., if commodity net quantity $< 10\text{g}$, is it exempt? If domestic package, is explicit Country of Origin exempt? If not exempt $\rightarrow$ **FAIL** (Missing mandatory declaration under Rule 6). |
| `status: "ambiguous"` | **Conflicting Declarations Warning**: Conflicting declarations across packaging views violate Rule 6(3) (ambiguous / misleading declarations). Evaluate `candidates[]` and flag as **WARNING / FAIL**. |

---

## 16. Backend Integration Notes (Person 3 / 4)

- **Import path:** `from analyzer import analyze_multi_image`
- **Execution model:** Synchronous CPU-bound inference. In FastAPI, invoke via `run_in_threadpool` or standard synchronous route functions to avoid blocking the asyncio event loop:
  ```python
  from fastapi.concurrency import run_in_threadpool
  from analyzer import analyze_multi_image

  @app.post("/api/v1/inspect")
  async def inspect_package(front_path: str, back_path: str, side_path: Optional[str] = None):
      result = await run_in_threadpool(
          analyze_multi_image,
          front_image_path=front_path,
          back_image_path=back_path,
          side_image_path=side_path,
          demo_mode=False
      )
      return result
  ```
- **Thread-safety:** PaddleOCR model inference is thread-safe for sequential requests. For high-concurrency production deployments, process pooling or worker-level queue isolation is recommended.
- **Model caching:** PaddleOCR weights are automatically loaded and cached in memory upon the first invocation; subsequent calls avoid reload overhead.

---

## 17. Dependencies & Runtime Environment

The AI Engine requires **Python 3.10.x** and the following packages (from [`requirements.txt`](file:///Users/priyanshu/legal-metrology-compliance/ai-engine/requirements.txt)):

```text
paddlepaddle==3.3.1
paddleocr==3.7.0
paddlex==3.7.2
opencv-python-headless==5.0.0.93
numpy==2.2.6
pytest==9.1.1
```

---

## 18. Test Status

As of September 5, 2026, the entire AI engine test suite is passing with zero errors or failures:

```bash
# Run all 79 tests across all engine modules
./venv/bin/python -m pytest tests/ -v

# Run 42 field extractor unit and regression tests
./venv/bin/python -m pytest tests/test_extractor.py -v

# Run 14 multi-image analyzer orchestration tests
./venv/bin/python -m pytest tests/test_analyzer.py -v
```

**Test Summary:**
- Total Tests: **79 passed** in ~121s.
- Regression Coverage: Includes real-product tests for Amul Butter, Lay's Potato Chips, promotional packs, joint MFD/EXP dates, narrow USP denominators, and negative brand name descriptor filtering.

---

## 19. File Map

```text
ai-engine/
├── analyzer.py               # Central orchestrator (analyze_image, analyze_multi_image)
├── analyze.py                # Command-line interface with single & multi-image flags
├── config.py                 # Field constants, labels, thresholds, dimension constraints
├── schemas.py                # Standard data models and result constructors
├── extractor.py              # 9-field extraction regexes, heuristics, and merge_detections()
├── preprocess.py             # OpenCV loading, aspect-preserving resize, grayscale, CLAHE
├── ocr.py                    # Local PaddleOCR wrapper with coordinate rescaling
├── readability.py            # Pixel-based text height and readability estimation
├── demo_fallback.py          # Deterministic demo fallback dataset for stage pitches
├── requirements.txt          # Pinned runtime dependencies
├── tests/
│   ├── test_analyzer.py      # Orchestration, multi-image, error-safety tests
│   ├── test_extractor.py     # 42 field extraction & merge unit tests
│   ├── test_ocr.py           # OCR format, filtering, and polygon tests
│   ├── test_preprocess.py    # Image validation, scaling, CLAHE tests
│   └── test_schemas.py       # JSON schema and status enum validation
└── samples/                  # Physical sample images for testing
```

---

## 20. Complete Real-Product JSON Output Example

Below is the actual JSON generated by running `analyze_multi_image()` on the Lay's Magic Masala product (`samples/1.jpg` + `samples/2.jpg`):

```json
{
  "success": true,
  "image_paths": {
    "front": "samples/1.jpg",
    "back": "samples/2.jpg",
    "side": null
  },
  "image_path": "samples/1.jpg",
  "image_id": "1",
  "timestamp": "2026-09-05T16:26:06.123456+00:00",
  "processing_time_ms": 1420,
  "raw_ocr": {
    "front": {
      "full_text": "—COLOU\n&FLAV\nS\nay\nTM\nINDIA'S\nMAGIC MASALA\nMADEWITH\nFINEST POTATOES",
      "line_count": 9,
      "avg_confidence": 0.9904,
      "ocr_results": [ /* Normalized OCR polygon items */ ]
    },
    "back": {
      "full_text": "OR CALL US AT 1800 22 4020\nCONSUMER.FEEDBACK@PEPSICO.COM\nMRP Rs. 10/- (INCL. OF ALL TAXES)\nUNIT SALE PRICE:\nRs. 0.33/- PER g\n25/08/26 & 07/01/27\nMFD & USE BY:\n30.5 g (28 g+2.5 g)",
      "line_count": 32,
      "avg_confidence": 0.9621,
      "ocr_results": [ /* Normalized OCR polygon items */ ]
    },
    "side": null
  },
  "detections": [
    {
      "field": "product_name",
      "label": "Product Name",
      "value": null,
      "raw_match": null,
      "confidence": 0.0,
      "bbox": null,
      "source": "ocr",
      "source_image": null,
      "status": "not_found"
    },
    {
      "field": "manufacturer_packer_importer",
      "label": "Manufacturer / Packer / Importer",
      "value": null,
      "raw_match": null,
      "confidence": 0.0,
      "bbox": null,
      "source": "ocr",
      "source_image": null,
      "status": "not_found"
    },
    {
      "field": "net_quantity",
      "label": "Net Quantity",
      "value": "30.5 g",
      "raw_match": "30.5 g (28 g+2.5 g)",
      "confidence": 0.8978,
      "bbox": [[866.0, 3426.0], [1225.0, 3431.0], [1223.0, 3549.0], [865.0, 3544.0]],
      "source": "ocr",
      "source_image": "back",
      "status": "found"
    },
    {
      "field": "mrp",
      "label": "Maximum Retail Price",
      "value": "10",
      "raw_match": "MRP Rs. 10/- (INCL. OF ALL TAXES)",
      "confidence": 0.9978,
      "bbox": [[87.0, 2868.0], [1359.0, 2796.0], [1365.0, 2898.0], [93.0, 2970.0]],
      "source": "ocr",
      "source_image": "back",
      "status": "found"
    },
    {
      "field": "manufacturing_date",
      "label": "Manufacturing / Packing Date",
      "value": "25/08/26",
      "raw_match": "25/08/26 & 07/01/27",
      "confidence": 0.998,
      "bbox": [[866.0, 3323.0], [1358.0, 3321.0], [1359.0, 3400.0], [866.0, 3402.0]],
      "source": "ocr",
      "source_image": "back",
      "status": "found"
    },
    {
      "field": "consumer_care",
      "label": "Consumer Care Details",
      "value": "1800 22 4020 | CONSUMER.FEEDBACK@PEPSICO.COM",
      "raw_match": "OR CALL US AT 1800 22 4020 | CONSUMER.FEEDBACK@PEPSICO.COM",
      "confidence": 0.9911,
      "bbox": [[75.0, 375.0], [1487.0, 375.0], [1487.0, 696.0], [75.0, 696.0]],
      "source": "ocr",
      "source_image": "back",
      "status": "found"
    },
    {
      "field": "country_of_origin",
      "label": "Country of Origin",
      "value": null,
      "raw_match": null,
      "confidence": 0.0,
      "bbox": null,
      "source": "ocr",
      "source_image": null,
      "status": "not_found"
    },
    {
      "field": "best_before",
      "label": "Best Before / Use By",
      "value": "07/01/27",
      "raw_match": "25/08/26 & 07/01/27",
      "confidence": 0.998,
      "bbox": [[866.0, 3323.0], [1358.0, 3321.0], [1359.0, 3400.0], [866.0, 3402.0]],
      "source": "ocr",
      "source_image": "back",
      "status": "found"
    },
    {
      "field": "unit_sale_price",
      "label": "Unit Sale Price",
      "value": "₹0.33 / g",
      "raw_match": "Rs. 0.33/- PER g",
      "confidence": 0.9601,
      "bbox": [[860.0, 3182.0], [1335.0, 3192.0], [1333.0, 3282.0], [859.0, 3272.0]],
      "source": "ocr",
      "source_image": "back",
      "status": "found"
    }
  ],
  "readability": {
    "front": { "avg_text_height_px": 178.7, "min_text_height_px": 54.0, "max_text_height_px": 518.0, "small_text_count": 0, "image_resolution": [2086, 2581], "estimated_readability": "good", "note": "..." },
    "back": { "avg_text_height_px": 88.8, "min_text_height_px": 29.0, "max_text_height_px": 179.0, "small_text_count": 0, "image_resolution": [2371, 3567], "estimated_readability": "good", "note": "..." },
    "side": null
  },
  "metadata": {
    "ocr_engine": "paddleocr",
    "images_supplied": ["front", "back"],
    "images_absent": ["side"],
    "preprocessing_applied": {
      "front": ["load", "grayscale", "clahe"],
      "back": ["load", "grayscale", "clahe"]
    },
    "demo_mode": false
  },
  "errors": []
}
```

---

## 21. Clear AI-vs-Legal Responsibility Boundary

To avoid architectural confusion, adhere strictly to the following division of responsibility:

| Aspect | Person 5 (AI Engine) Responsibility | Person 6 (Compliance Rules Engine) Responsibility |
|---|---|---|
| **Text Detection** | Reads raw glyphs and characters via PaddleOCR. | Does not run OCR. Consumes extracted values. |
| **Field Extraction** | Applies deterministic regex & heuristics to find declaration values. | Does not parse raw images. Consumes structured detection objects. |
| **Field Missing (`not_found`)** | Reports `status: "not_found"` when no pattern matches. | Determines whether the absence is a legal violation (FAIL), permissible warning, or exempt. |
| **Unit Verification** | Normalizes units (`gms` $\rightarrow$ `g`, `mL` $\rightarrow$ `ml`). | Evaluates whether normalized unit is approved under Rule 5 (e.g., solid goods in `g`/`kg`, liquids in `ml`/`l`). |
| **Font Size Measurement** | Measures bounding box heights in pixels. | Owns Rule 9 font height compliance. (Note: physical mm cannot be calculated from pixels without calibration). |
| **Ambiguity Conflict** | Reports both conflicting values in `candidates[]`. | Decides legal implication of conflicting label information (Rule 6(3) deceptive packaging). |
| **Legal Scoring** | None. Returns zero PASS/FAIL tokens. | Computes numerical compliance score (0–100%), violation severity (CRITICAL, MAJOR, MINOR), and final PASS/FAIL verdict. |

---

## PERSON 6 QUICK HANDOFF

```python
# 1. Exact Function to Call
from analyzer import analyze_multi_image

# 2. Exact Arguments
result = analyze_multi_image(
    front_image_path="path/to/front.jpg",
    back_image_path="path/to/back.jpg",
    side_image_path="path/to/side.jpg",  # Optional, pass None if unavailable
    demo_mode=False                       # Keep False for production rules
)

# 3. Exact Key to Feed to Rules
detections = result["detections"]  # List of 9 detection dicts

# 4. Meaning of Detection Statuses
# - item["status"] == "found": Field present. Value is in item["value"]. Run legal checks.
# - item["status"] == "low_confidence": Possible OCR blur. Value is in item["value"]. Flag warning.
# - item["status"] == "not_found": Declaration absent. item["value"] is None. Evaluate Rule 6 violation.
# - item["status"] == "ambiguous": Conflicting values across views. Check item["candidates"].

# 5. Golden Rules for Person 6:
# - NEVER assume not_found equals FAIL: You must check exemptions (e.g., small pack exemptions, domestic address vs origin).
# - NEVER use readability for Rule 9 font mm size: Readability is pixel-based only.
# - NEVER assume OCR confidence equals legal validity: Confidence only reflects character legibility.
```
