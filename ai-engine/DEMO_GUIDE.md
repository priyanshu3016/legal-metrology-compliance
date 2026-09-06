# SIH 2026 — Live Presentation & Demo Script (Person 5 / AI Engine)

> **Module:** AI Engine (OCR + Mandatory Declarations Extraction)  
> **Prepared by:** Person 5  
> **Target Audience:** Hackathon Evaluators, Jury, Pitch Presentation

---

## 1. Demo Flow Summary

During the pitch, we demonstrate the end-to-end pipeline on **live commodity images**:
1. Image is provided to the system.
2. Preprocessing dynamically balances contrast (CLAHE) and resizes for optimal character detection.
3. PaddleOCR local inference runs with zero cloud dependencies.
4. Deterministic extractors parse and normalize all 9 Legal Metrology mandatory fields.
5. Structured JSON is returned to the Rules Engine (Person 6) and Dashboard (Persons 1 & 2).

---

## 2. Recommended Presentation Sequence (Ordered Demo Script)

| Step | Image Path | Category | Expected Demonstration |
|:---:|---|---|---|
| **1** | `samples/compliant/demo_product_01.jpg` | **Compliant** | **Happy Path:** Parle-G Gold Biscuits. All 9 mandatory fields present with high confidence. Shows 4-point bounding boxes for visual evidence. |
| **2** | `samples/compliant/demo_product_02.jpg` | **Compliant** | **Liquid Beverage:** Real Mixed Fruit Juice. Correctly extracts volume (`1 l`) and unit price (`₹0.13 / ml`). |
| **3** | `samples/noncompliant/demo_product_06.jpg` | **Violation** | **Missing MRP:** Kurkure Masala Munch. System flags MRP as `not_found`. Triggers Person 6's rule violation alert. |
| **4** | `samples/noncompliant/demo_product_07.jpg` | **Violation** | **Missing Manufacturer:** Everest Garam Masala. Manufacturer field flagged as `not_found`. |
| **5** | `samples/compliant/demo_product_05.jpg` | **Imported** | **Country of Origin Verification:** Ferrero Rocher. Captures `Country of Origin: Italy` and `Imported by: Ferrero India`. |

---

## 3. Quick Terminal Commands for Live Demonstration

### Run Live Analysis on Compliant Product
```bash
python analyze.py samples/compliant/demo_product_01.jpg
```

### Run Live Analysis on Non-Compliant Product (Missing MRP)
```bash
python analyze.py samples/noncompliant/demo_product_06.jpg
```

### Force Demo Mode (Fail-safe Safety Net)
If venue camera or projector lighting causes unexpected glare:
```bash
python analyze.py samples/compliant/demo_product_01.jpg --demo
```

---

## 4. Key Talking Points for Judges

1. **100% Local Inference:** No cloud API latency or ongoing cost; data remains private on-device.
2. **Apple Silicon Native:** Hardware accelerated via M-series optimized execution.
3. **Evidence-Ready:** Every extraction preserves 4-point polygon bounding boxes mapped back to the original image dimensions for visual bounding overlays.
4. **Resilient to Optical Errors:** Includes automatic regex tolerance, unit normalization, and optical character typo corrections.
