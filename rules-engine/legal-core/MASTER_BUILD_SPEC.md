# MASTER BUILD SPECIFICATION

## Smart India Hackathon 2026 — PS 34
### Software System to Check Compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011

**Version:** 1.0  
**Date:** 2026-09-05  
**Status:** AUTHORITATIVE — This is the single source of truth for all coding agents.

---

# TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Exact Interpretation of the Problem Statement](#2-exact-interpretation-of-the-problem-statement)
3. [Legal Document Analysis](#3-legal-document-analysis)
4. [Final Regulatory Rule Matrix](#4-final-regulatory-rule-matrix)
5. [MVP Compliance Checks](#5-mvp-compliance-checks)
6. [RAG Architecture](#6-rag-architecture)
7. [OCR to Structured Data Contract](#7-ocr-to-structured-data-contract)
8. [Compliance Engine Architecture](#8-compliance-engine-architecture)
9. [Human Review Architecture](#9-human-review-architecture)
10. [Evidence and Explainability](#10-evidence-and-explainability)
11. [Database Schema](#11-database-schema)
12. [API Contract](#12-api-contract)
13. [Frontend Specification](#13-frontend-specification)
14. [Repository Structure](#14-repository-structure)
15. [Team Responsibilities](#15-team-responsibilities)
16. [Demo Dataset](#16-demo-dataset)
17. [Testing Strategy](#17-testing-strategy)
18. [Five-Day Development Plan](#18-five-day-development-plan)
19. [Demo Flow](#19-demo-flow)
20. [MVP vs Future Scope](#20-mvp-vs-future-scope)
21. [Risks and Mitigations](#21-risks-and-mitigations)
22. [Coding Agent Instructions](#22-coding-agent-instructions)
23. [Final End-to-End Architecture](#23-final-end-to-end-architecture)
24. [Acceptance Criteria](#24-acceptance-criteria)
25. [Final Checklist Before SIH Demonstration](#25-final-checklist-before-sih-demonstration)

---

# 1. Executive Summary

We are building an AI-assisted compliance-checking platform for packaged commodities under the Legal Metrology (Packaged Commodities) Rules, 2011 (made under the Legal Metrology Act, 2009).

**What it does:**
1. Accepts a photograph of a packaged commodity
2. Extracts text and declarations via OCR
3. Structures the extracted information into normalized fields
4. Retrieves relevant legal requirements from a RAG-indexed legal corpus
5. Runs deterministic compliance checks comparing extracted facts against legal requirements
6. Returns PASS / FAIL / REVIEW for each check with full explainability
7. Generates an inspection-ready report
8. Supports human-in-the-loop review for uncertain cases
9. Maintains inspection history with dashboard analytics

**What it is NOT:**
- NOT a legally binding compliance certificate
- NOT an IMAGE-to-LLM-to-"legal/illegal" black box
- NOT a replacement for physical inspection
- It IS an "AI-assisted preliminary compliance assessment" tool

**Technology Stack:**
- **Backend:** Python + FastAPI
- **Database:** SQLite (dev) / PostgreSQL (production-ready schema)
- **OCR:** Google Cloud Vision API or Tesseract with preprocessing
- **RAG:** PyMuPDF + sentence-transformers + ChromaDB
- **LLM (assist):** Google Gemini API (for explanation generation and semantic extraction)
- **Frontend:** React (Vite) with modern CSS
- **Report:** HTML/PDF generation

---

# 2. Exact Interpretation of the Problem Statement

**PS 34:** *"Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels."*

### Interpretation:

| PS Phrase | Our Interpretation |
|---|---|
| "Software System" | Web application with backend API, frontend UI, database, and AI pipeline |
| "check compliance" | Compare extracted product declarations against legal requirements; issue PASS/FAIL/REVIEW with evidence |
| "Packaged Commodities" | Pre-packaged commodities intended for retail sale as defined in the 2011 Rules (Rule 2(k) — retail package) |
| "under Legal Metrology (Packaged Commodities) Rules, 2011" | The primary regulatory corpus is the 2011 Rules, with the parent Legal Metrology Act, 2009 providing the enabling framework and penalty provisions |
| "by scanning products, images and labels" | Input is a photograph/image of the product package; the system uses OCR and computer vision to extract visible information |

### What is NOT in scope for the MVP:
- Live video scanning
- Barcode/QR code-based lookup (future scope)
- Physical quantity verification (requires weighing/measuring equipment)
- FSSAI / Drugs & Cosmetics / other sector-specific regulations
- Multi-product batch scanning
- Mobile native application (web-responsive is sufficient)

---

# 3. Legal Document Analysis

**Fully documented in [RULE_MATRIX.md](file:///c:/Users/Ritika%20Soni/OneDrive/Desktop/SIH_PS34/RULE_MATRIX.md).**

Key findings:

1. `rules2009.pdf` is the **Legal Metrology Act, 2009** — the parent statute
2. `rules2011.pdf` is the **Legal Metrology (Packaged Commodities) Rules, 2011** — the operational rules
3. The 2011 Rules Chapter II (Rules 3-23) contains all label declaration requirements
4. Rule 6 is the central rule — mandates 7 categories of declarations
5. 30 requirements were inventoried; 10 are clearly image-detectable; 10 partially; 10 not at all
6. 8 MVP rules + 2 optional rules were selected for the prototype
7. 5 ambiguities were identified and documented with decisions

---

# 4. Final Regulatory Rule Matrix

**Fully documented in [RULE_MATRIX.md](file:///c:/Users/Ritika%20Soni/OneDrive/Desktop/SIH_PS34/RULE_MATRIX.md).**

Summary of selected rules:

| ID | Check | Source | Severity | Type |
|---|---|---|---|---|
| CHK-01 | Product Name Present | Rule 6(1)(b) | CRITICAL | Presence |
| CHK-02 | Net Quantity Valid | Rule 6(1)(c), 13 | CRITICAL | Presence+Format+Unit |
| CHK-03 | MRP Present & Formatted | Rule 6(1)(e), 2(m) | CRITICAL | Presence+Format |
| CHK-04 | Manufacturer/Packer/Importer | Rule 6(1)(a), 10 | CRITICAL | Presence |
| CHK-05 | Manufacturing Date | Rule 6(1)(d) | HIGH | Presence+Format |
| CHK-06 | Consumer Care Info | Rule 6(2) | HIGH | Presence+Pattern |
| CHK-07 | No Misleading Qualifiers | Rule 12(6) | MEDIUM | Keyword |
| CHK-08 | Language (Hindi/English) | Rule 9(4) | MEDIUM | Script Detection |
| CHK-09 | Country of Origin (imports) | Rule 6(1)(a), 10(1) | HIGH | Conditional |
| CHK-10 | MRP Sticker Check | Rule 6(3), 18(5) | HIGH | Multi-value |

---

# 5. MVP Compliance Checks

The 8 MVP checks (CHK-01 through CHK-07 and CHK-09) form the minimum viable compliance engine. Each check:

1. Takes structured OCR facts as input
2. Applies deterministic validation logic
3. Returns a result with status, confidence, evidence, and legal citation
4. Can explain its reasoning

**Validation Categories:**

| Category | Checks | Logic |
|---|---|---|
| **Presence** | CHK-01, CHK-04, CHK-05, CHK-06 | Field is non-null/non-empty with sufficient confidence |
| **Presence + Format** | CHK-02, CHK-03 | Field present AND matches expected format/pattern |
| **Keyword** | CHK-07 | Prohibited words NOT found near specific field |
| **Conditional** | CHK-09 | IF condition X THEN field Y must be present |

---

# 6. RAG Architecture

## 6.1 Why RAG

RAG serves two purposes:
1. **Retrieval:** Given a product being inspected, retrieve the specific legal provisions that apply
2. **Citation:** Provide traceable legal source references for every compliance finding

The legal corpus is small (2 PDFs, ~61 pages total), but RAG is architecturally important because:
- It demonstrates a maintainable, extensible approach (new regulations can be added)
- It provides source citations that a judge/inspector can verify
- It separates legal knowledge from application logic

## 6.2 RAG Pipeline

```
PDF Files (rules2009.pdf, rules2011.pdf)
    |
    v
[1] PDF Ingestion (PyMuPDF)
    |
    v
[2] Text Extraction (page-by-page, preserving page numbers)
    |
    v
[3] Cleaning (normalize whitespace, fix OCR artifacts, handle table formatting)
    |
    v
[4] Section/Rule-Aware Chunking
    |  - Split by Rule number (regex: /^\d+\./)
    |  - Each chunk = one rule or sub-rule
    |  - Preserve cross-references
    |  - Schedules chunked separately
    |
    v
[5] Metadata Extraction
    |  - document_name
    |  - rule_number
    |  - sub_rule (if applicable)
    |  - chapter
    |  - page_number
    |  - section_title
    |  - chunk_type (rule | schedule | definition | proviso | explanation)
    |
    v
[6] Embedding Generation (sentence-transformers: all-MiniLM-L6-v2)
    |
    v
[7] Vector Database (ChromaDB, persistent storage)
    |
    v
[8] Retrieval (similarity search with metadata filtering)
    |  - Query: constructed from product fields + check type
    |  - Filter: by document, chapter, chunk_type
    |  - Top-K: 5 chunks
    |
    v
[9] Reranking (optional: cross-encoder reranking for top results)
    |
    v
[10] Context Assembly
    |   - Combine retrieved chunks
    |   - Add metadata for citation
    |
    v
[11] Output: Retrieved legal requirements with citations
```

## 6.3 Technology Choices

| Component | Technology | Why |
|---|---|---|
| PDF extraction | PyMuPDF (pymupdf) | Fast, reliable, pure Python, page-aware |
| Chunking | Custom Python (regex-based) | Legal text has predictable structure (numbered rules); generic chunkers would destroy rule boundaries |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Small (80MB), fast, runs locally, no API costs, good for short passages |
| Vector DB | ChromaDB | Zero-config, embedded, persistent, Python-native, supports metadata filtering |
| Reranking | Optional: `cross-encoder/ms-marco-MiniLM-L-6-v2` | Only if retrieval quality needs improvement |

**What we are NOT using:**
- LangChain / LlamaIndex: Unnecessary abstraction for our small, well-structured corpus. Direct PyMuPDF + ChromaDB is simpler and more transparent.
- FAISS: ChromaDB provides a simpler API with built-in metadata filtering. FAISS would require more boilerplate.
- Cloud vector databases: No need for a 61-page corpus.

## 6.4 Chunking Strategy

The legal documents have a clear hierarchical structure:

```
Act / Rules
  Chapter
    Rule (numbered: 1, 2, 3, ...)
      Sub-rule (numbered: (1), (2), (3), ...)
        Clause (lettered: (a), (b), (c), ...)
          Proviso ("Provided that...")
          Explanation ("Explanation.- ...")
  Schedule
    Table
    Items
```

**Chunking rules:**
1. **Primary split:** By Rule number. Each Rule becomes one or more chunks.
2. **Secondary split:** If a Rule is very long (>1000 chars), split by sub-rule.
3. **Schedules:** Each Schedule is one chunk, unless it contains a table — then the table is a separate chunk with the schedule header as context.
4. **Definitions:** Rule 2 (Definitions) — each definition is a separate chunk.
5. **Provisos and Explanations:** Keep attached to their parent rule/sub-rule chunk.

**Chunk overlap:** 1-2 sentences of preceding context (the rule/sub-rule header) for continuity.

## 6.5 Query Construction

When checking a specific product, the RAG query is constructed as:

```python
def build_rag_query(check_id: str, product_context: dict) -> str:
    queries = {
        "CHK-01": "packaged commodity name declaration requirement retail package label",
        "CHK-02": "net quantity declaration standard units weight measure SI units",
        "CHK-03": "maximum retail price MRP declaration inclusive of all taxes format",
        "CHK-04": "manufacturer packer importer name address declaration package",
        "CHK-05": "month year manufacture packing date declaration package",
        "CHK-06": "consumer complaint contact telephone email address package",
        "CHK-07": "quantity declaration misleading words minimum approximate average",
        "CHK-09": "imported package country origin importer name address",
    }
    query = queries.get(check_id, "")
    if product_context.get("is_imported"):
        query += " imported goods importer"
    return query
```

## 6.6 Retrieval Result Format

```json
{
  "query": "...",
  "results": [
    {
      "chunk_id": "rules2011_rule6_1_b",
      "text": "The common or generic names of the commodity...",
      "metadata": {
        "document": "rules2011.pdf",
        "document_title": "Legal Metrology (Packaged Commodities) Rules, 2011",
        "rule": "6",
        "sub_rule": "1",
        "clause": "b",
        "chapter": "II",
        "page": 5,
        "chunk_type": "rule",
        "section_title": "Declarations to be made on every package"
      },
      "similarity_score": 0.87
    }
  ]
}
```

## 6.7 Citation Format

For frontend display and reports:

```
Rule 6(1)(b), The Legal Metrology (Packaged Commodities) Rules, 2011 (Page 5)
```

---

# 7. OCR to Structured Data Contract

## 7.1 Input to OCR Pipeline

```json
{
  "image": "<base64_encoded_image or file_path>",
  "image_id": "uuid",
  "preprocessing_options": {
    "auto_rotate": true,
    "enhance_contrast": true,
    "denoise": true
  }
}
```

## 7.2 OCR Output — Structured Product Facts

This is the **canonical interface** between the OCR component and the Compliance Engine. Both teams MUST conform to this schema.

```json
{
  "ocr_id": "uuid",
  "image_id": "uuid",
  "timestamp": "ISO-8601",
  "overall_confidence": 0.85,
  "image_quality": "good|fair|poor",
  "raw_text": "Full OCR text as a single string",
  "fields": {
    "product_name": {
      "value": "Parle-G Gold Biscuits",
      "confidence": 0.92,
      "raw_text": "PARLE-G GOLD",
      "bounding_box": {"x": 120, "y": 50, "width": 300, "height": 40},
      "source": "ocr"
    },
    "net_quantity": {
      "value": {
        "numeric": 200.0,
        "unit": "g",
        "raw_unit": "g"
      },
      "confidence": 0.95,
      "raw_text": "Net Wt. 200g",
      "bounding_box": {"x": 150, "y": 400, "width": 100, "height": 25},
      "source": "ocr"
    },
    "mrp": {
      "value": {
        "amount": 20.0,
        "currency": "INR",
        "includes_tax": true,
        "tax_declaration_text": "inclusive of all taxes"
      },
      "confidence": 0.90,
      "raw_text": "MRP Rs. 20.00 (incl. of all taxes)",
      "bounding_box": {"x": 100, "y": 450, "width": 250, "height": 25},
      "source": "ocr"
    },
    "manufacturer": {
      "value": {
        "name": "Parle Products Pvt. Ltd.",
        "address": "Vile Parle (East), Mumbai - 400057",
        "role": "manufacturer"
      },
      "confidence": 0.88,
      "raw_text": "Mfd. by: Parle Products Pvt. Ltd., Vile Parle (East), Mumbai - 400057",
      "bounding_box": {"x": 50, "y": 500, "width": 400, "height": 60},
      "source": "ocr"
    },
    "packer": {
      "value": null,
      "confidence": null,
      "raw_text": null,
      "bounding_box": null,
      "source": "ocr"
    },
    "importer": {
      "value": null,
      "confidence": null,
      "raw_text": null,
      "bounding_box": null,
      "source": "ocr"
    },
    "manufacturing_date": {
      "value": {
        "month": 8,
        "year": 2026,
        "day": null,
        "format": "MM/YYYY"
      },
      "confidence": 0.85,
      "raw_text": "Mfg. Date: 08/2026",
      "bounding_box": {"x": 50, "y": 560, "width": 180, "height": 20},
      "source": "ocr"
    },
    "expiry_date": {
      "value": {
        "month": 2,
        "year": 2027,
        "day": null,
        "format": "MM/YYYY"
      },
      "confidence": 0.85,
      "raw_text": "Best Before: 02/2027",
      "bounding_box": {"x": 50, "y": 580, "width": 180, "height": 20},
      "source": "ocr"
    },
    "consumer_care": {
      "value": {
        "phone": "1800-123-4567",
        "email": "consumer@parle.com",
        "address": null
      },
      "confidence": 0.82,
      "raw_text": "Consumer Care: 1800-123-4567, consumer@parle.com",
      "bounding_box": {"x": 50, "y": 620, "width": 350, "height": 30},
      "source": "ocr"
    },
    "country_of_origin": {
      "value": null,
      "confidence": null,
      "raw_text": null,
      "bounding_box": null,
      "source": "ocr"
    },
    "batch_number": {
      "value": "B2608A",
      "confidence": 0.78,
      "raw_text": "Batch: B2608A",
      "bounding_box": {"x": 250, "y": 560, "width": 120, "height": 20},
      "source": "ocr"
    },
    "fssai_license": {
      "value": "10012345678901",
      "confidence": 0.80,
      "raw_text": "FSSAI Lic. No. 10012345678901",
      "bounding_box": {"x": 50, "y": 650, "width": 250, "height": 20},
      "source": "ocr"
    }
  },
  "quantity_qualifiers_detected": [],
  "detected_languages": ["en"],
  "all_detected_mrp_values": [
    {
      "amount": 20.0,
      "raw_text": "MRP Rs. 20.00",
      "bounding_box": {"x": 100, "y": 450, "width": 250, "height": 25}
    }
  ]
}
```

### 7.3 Field Rules

| Rule | Detail |
|---|---|
| **Missing values** | Use `null` for value, confidence, raw_text, and bounding_box. Do NOT use strings like "not found" or "N/A". |
| **Confidence** | Float 0.0–1.0. Represents OCR confidence for the specific field extraction. |
| **Bounding box** | Pixel coordinates relative to the input image. Optional but strongly recommended for evidence. |
| **Source** | Always "ocr" for OCR-extracted fields. Future: could be "barcode", "manual", etc. |
| **Additional fields** | Fields like `batch_number`, `fssai_license`, `ingredients` are extracted if found but are NOT part of the 2011 Rules compliance checks. They are informational. |
| **quantity_qualifiers_detected** | Array of prohibited qualifier words (per CHK-07) found near quantity text. Empty array if none. |
| **all_detected_mrp_values** | Array of ALL MRP-like values found (for CHK-10). Usually 1 element. |

### 7.4 OCR Technology Choice

**Primary recommendation:** Google Cloud Vision API
- Excellent accuracy on Indian product labels
- Handles Hindi/Devanagari
- Returns bounding boxes
- Free tier: 1000 images/month

**Fallback:** Tesseract OCR with preprocessing
- Free, offline
- Requires image preprocessing (deskew, contrast, denoise)
- Lower accuracy on complex labels
- Suitable for demo if API keys are not available

**OCR post-processing:** An LLM (Gemini) assists in structuring raw OCR text into the fields above. The LLM receives the raw OCR text and extracts structured fields. This is NOT the compliance decision — it is data extraction.

### 7.5 LLM-Assisted Extraction Prompt

```
You are a structured data extractor for Indian packaged commodity labels.

Given the following OCR-extracted text from a product package, extract the fields listed below.

For each field, provide:
- value: the extracted value (null if not found)
- raw_text: the exact text from which you extracted it
- confidence: your confidence (0.0-1.0)

Fields to extract:
1. product_name - the common or generic name of the product
2. net_quantity - numeric value and unit (e.g., {"numeric": 200, "unit": "g"})
3. mrp - Maximum Retail Price with tax inclusion status
4. manufacturer - name, address, role (manufacturer/packer/importer)
5. packer - if different from manufacturer
6. importer - if present
7. manufacturing_date - month and year
8. expiry_date / best_before - if present
9. consumer_care - phone, email, address for complaints
10. country_of_origin - if present
11. batch_number - if present
12. fssai_license - if present

Also identify:
- quantity_qualifiers: any words like "minimum", "approximately", "about" near the quantity declaration
- all_mrp_values: all instances of MRP-like values found

OCR Text:
{raw_ocr_text}

Respond in JSON format only.
```

---

# 8. Compliance Engine Architecture

## 8.1 Overview

The Compliance Engine is the **deterministic core** of the system. It does NOT use an LLM to make compliance decisions. It applies rule-by-rule validation logic against structured facts.

```
Structured OCR Facts (Section 7)
    +
Product Context (category hints, import indicators)
    +
Retrieved Legal Requirements (from RAG, Section 6)
    +
Rule Matrix (from RULE_MATRIX.md)
    |
    v
Compliance Engine
    |
    v
Compliance Result (per-check results + overall status)
```

## 8.2 Input Schema

```json
{
  "inspection_id": "uuid",
  "ocr_facts": { /* Section 7.2 schema */ },
  "product_context": {
    "category_hint": "food|cosmetics|household|electronics|general|unknown",
    "is_imported": false,
    "is_exempt": false
  },
  "retrieved_legal_context": [
    {
      "check_id": "CHK-01",
      "legal_text": "...",
      "citation": "Rule 6(1)(b), LM(PC) Rules, 2011",
      "page": 5
    }
  ],
  "active_rules": ["CHK-01", "CHK-02", "CHK-03", "CHK-04", "CHK-05", "CHK-06", "CHK-07", "CHK-09"]
}
```

## 8.3 Output Schema

```json
{
  "inspection_id": "uuid",
  "timestamp": "ISO-8601",
  "overall_status": "PASS|FAIL|REVIEW",
  "summary": {
    "total_checks": 8,
    "passed": 6,
    "failed": 1,
    "review": 1,
    "compliance_score": 75.0
  },
  "checks": [
    {
      "check_id": "CHK-01",
      "rule_name": "Product Name Declaration",
      "status": "PASS",
      "severity": "CRITICAL",
      "detected_value": "Parle-G Gold Biscuits",
      "expected": "Non-empty product/commodity name",
      "confidence": 0.92,
      "reason": "Product name 'Parle-G Gold Biscuits' detected on the package with high confidence.",
      "evidence": {
        "raw_text": "PARLE-G GOLD",
        "bounding_box": {"x": 120, "y": 50, "width": 300, "height": 40},
        "source": "ocr"
      },
      "legal_source": {
        "citation": "Rule 6(1)(b), The Legal Metrology (Packaged Commodities) Rules, 2011",
        "page": 5,
        "text": "The common or generic names of the commodity contained in the package..."
      },
      "recommendation": null
    },
    {
      "check_id": "CHK-06",
      "rule_name": "Consumer Care Information",
      "status": "FAIL",
      "severity": "HIGH",
      "detected_value": null,
      "expected": "Phone number, email, or address for consumer complaints",
      "confidence": 0.85,
      "reason": "No consumer care contact information (phone, email, or complaint address) was detected on the visible portion of the package. Note: This information may be present on another face of the package not visible in the image.",
      "evidence": {
        "raw_text": null,
        "bounding_box": null,
        "source": "ocr_absence"
      },
      "legal_source": {
        "citation": "Rule 6(2), The Legal Metrology (Packaged Commodities) Rules, 2011",
        "page": 7,
        "text": "Every package shall bear the name, address, telephone number, e mail address..."
      },
      "recommendation": "Verify by inspecting all faces of the physical package. If consumer care information is genuinely absent, this is a violation under Rule 6(2)."
    }
  ],
  "disclaimers": [
    "This is an AI-assisted preliminary compliance assessment. It is not a legally binding judgment.",
    "OCR-based detection may miss information present on other faces of the package.",
    "Physical inspection by an authorized Legal Metrology Officer is recommended for official enforcement."
  ]
}
```

## 8.4 Validation Pipeline

```python
def run_compliance_check(check_id, ocr_facts, product_context, legal_context):
    """
    Each check follows this pipeline:
    1. EXTRACT: Get the relevant field from ocr_facts
    2. NORMALIZE: Clean/parse the extracted value
    3. VALIDATE: Apply the rule-specific logic
    4. DETERMINE STATUS: PASS / FAIL / REVIEW based on value + confidence
    5. GENERATE EVIDENCE: Package the evidence
    6. CITE: Attach legal source from RAG
    7. EXPLAIN: Generate human-readable explanation
    """
    pass
```

## 8.5 Status Determination Logic

| Scenario | Status | Rationale |
|---|---|---|
| Field found, valid, confidence >= 0.7 | **PASS** | High-confidence positive detection |
| Field NOT found, image confidence >= 0.8 | **FAIL** | High-confidence absence in a clear image |
| Field NOT found, image confidence < 0.8 | **REVIEW** | Cannot reliably determine if absent or undetected |
| Field found but confidence < 0.7 | **REVIEW** | Detected but uncertain |
| Field found, format invalid | **FAIL** | Present but non-compliant |
| Conditional rule, condition not met | **N/A** | Rule does not apply; skip |
| Exempt product | **N/A** | Product exempt from this rule |

## 8.6 Overall Status Calculation

```python
def calculate_overall_status(check_results):
    statuses = [r["status"] for r in check_results if r["status"] != "N/A"]
    if any(s == "FAIL" for s in statuses):
        return "FAIL"
    elif any(s == "REVIEW" for s in statuses):
        return "REVIEW"
    else:
        return "PASS"
```

## 8.7 Compliance Score

```python
def calculate_score(check_results):
    """
    Prototype summary score. NOT a legal metric.
    Weights: CRITICAL=3, HIGH=2, MEDIUM=1
    Score = (sum of weighted passes) / (sum of all weights) * 100
    """
    weights = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}
    applicable = [r for r in check_results if r["status"] != "N/A"]
    total_weight = sum(weights.get(r["severity"], 1) for r in applicable)
    pass_weight = sum(weights.get(r["severity"], 1) for r in applicable if r["status"] == "PASS")
    return round((pass_weight / total_weight) * 100, 1) if total_weight > 0 else 0.0
```

## 8.8 Critical Distinctions

| Concept | Meaning |
|---|---|
| **Failed requirement** | The field was detected or its absence was confirmed with high confidence, AND it violates the rule |
| **OCR uncertainty** | The OCR could not reliably extract the field (low confidence, poor image quality) |
| **Rule uncertainty** | The rule's applicability to this product is uncertain (e.g., conditional rule, unknown category) |
| **Manual review** | A human inspector should verify the finding before it becomes an official determination |

---

# 9. Human Review Architecture

## 9.1 When Review is Triggered

A check gets REVIEW status when:
1. OCR confidence is low (< 0.7 for detected field; < 0.8 for overall image when field is absent)
2. Rule applicability is uncertain (conditional rules, unknown product category)
3. Image quality is poor
4. Multiple conflicting values detected (e.g., multiple MRPs)

## 9.2 Inspector Capabilities

The inspector should be able to:
1. **View** the original image with highlighted regions
2. **See** the extracted value and OCR confidence
3. **See** the relevant legal rule and its text
4. **Override** the AI result (change REVIEW to PASS or FAIL)
5. **Correct** the extracted value (enter the correct value)
6. **Add notes** explaining the decision
7. **Save** the final inspection result

## 9.3 Review Action Data Structure

```json
{
  "review_id": "uuid",
  "inspection_id": "uuid",
  "check_id": "CHK-06",
  "original_status": "REVIEW",
  "reviewer_action": "OVERRIDE_TO_PASS",
  "corrected_value": "1800-123-4567",
  "reviewer_notes": "Consumer care number is visible on the back panel of the package (not visible in the scanned image).",
  "reviewer_id": "inspector-001",
  "reviewed_at": "ISO-8601",
  "final_status": "PASS"
}
```

## 9.4 Review Status Flow

```
AI Result: REVIEW
    |
    v
Inspector reviews evidence
    |
    +---> OVERRIDE_TO_PASS (with notes)
    |
    +---> OVERRIDE_TO_FAIL (with notes)
    |
    +---> CONFIRM_REVIEW (needs further investigation)
    |
    +---> CORRECT_VALUE (enter correct value, re-evaluate)
```

---

# 10. Evidence and Explainability

## 10.1 Evidence Types

| Type | Description | When Used |
|---|---|---|
| **ocr_detection** | Text was detected by OCR at a specific location | Field found |
| **ocr_absence** | OCR did not find the expected text anywhere in the image | Field not found |
| **pattern_match** | A specific pattern (regex) was matched or not matched | Format validation |
| **keyword_detection** | A specific keyword was found or not found | Qualifier search |
| **image_region** | A region of the image is relevant (bounding box) | Visual evidence |

## 10.2 Evidence Structure

```json
{
  "type": "ocr_detection|ocr_absence|pattern_match|keyword_detection|image_region",
  "raw_text": "the exact OCR text or null",
  "bounding_box": {"x": 0, "y": 0, "width": 0, "height": 0},
  "confidence": 0.9,
  "description": "Human-readable description of what the evidence shows",
  "image_region_url": "/api/inspection/{id}/evidence/{check_id}/image"
}
```

## 10.3 Image Annotation

For evidence visualization, the system should:

1. **Highlight detected declarations** — Draw green bounding boxes around fields that PASS
2. **Highlight violations** — Draw red bounding boxes around fields that FAIL
3. **Highlight uncertain regions** — Draw yellow bounding boxes around fields that are REVIEW
4. **Overlay field labels** — Label each bounding box with the field name

This creates an annotated version of the original image that visually shows what was detected.

**Implementation:** Use Pillow (PIL) to draw rectangles on a copy of the original image.

## 10.4 Explainability Response Format

For each check, the system can answer "Why did you mark this?" with:

```json
{
  "question": "Why was this marked as FAIL?",
  "answer": "The MRP (Maximum Retail Price) was detected on the package as 'MRP Rs. 20.00', but the required declaration 'inclusive of all taxes' or equivalent was not found near the MRP value. Rule 2(m) of the Legal Metrology (Packaged Commodities) Rules, 2011 prescribes the format as 'MRP Rs. _____ incl. of all taxes'.",
  "detected_value": "MRP Rs. 20.00",
  "expected": "MRP Rs. _____ inclusive of all taxes",
  "legal_rule": "Rule 2(m), Rule 6(1)(e)",
  "legal_text": "'Maximum or Max. retail price Rs/... inclusive of all taxes or in the form MRP Rs/... incl., of all taxes'",
  "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
  "source_page": 3
}
```

## 10.5 Honesty Constraints

1. **Do NOT claim the image proves something it cannot.** If OCR did not find a field, say "not detected in the visible portion of the package" — not "absent from the package."
2. **Do NOT generate fake evidence.** Bounding boxes must correspond to actual OCR detections.
3. **Do NOT present OCR uncertainty as a definitive violation.**
4. **Always include disclaimers** about the preliminary nature of the assessment.

---

# 11. Database Schema

## 11.1 Entity Relationship

```
users (1) ---< (many) inspections
inspections (1) ---< (many) compliance_checks
compliance_checks (1) ---< (many) review_actions
inspections (1) ---< (many) extracted_fields
legal_chunks (reference table, loaded at startup)
```

## 11.2 Tables

### users

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('inspector', 'admin', 'viewer')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### inspections

```sql
CREATE TABLE inspections (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL REFERENCES users(id),
    image_path TEXT NOT NULL,
    annotated_image_path TEXT,
    product_name TEXT,
    category_hint TEXT DEFAULT 'unknown',
    overall_status TEXT CHECK (overall_status IN ('PASS', 'FAIL', 'REVIEW', 'PENDING')),
    compliance_score REAL,
    total_checks INTEGER DEFAULT 0,
    passed_checks INTEGER DEFAULT 0,
    failed_checks INTEGER DEFAULT 0,
    review_checks INTEGER DEFAULT 0,
    ocr_confidence REAL,
    raw_ocr_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_path TEXT,
    notes TEXT
);
CREATE INDEX idx_inspections_user ON inspections(user_id);
CREATE INDEX idx_inspections_status ON inspections(overall_status);
CREATE INDEX idx_inspections_created ON inspections(created_at);
```

### extracted_fields

```sql
CREATE TABLE extracted_fields (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    inspection_id TEXT NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    field_value TEXT,
    confidence REAL,
    raw_text TEXT,
    bounding_box_json TEXT,
    source TEXT DEFAULT 'ocr'
);
CREATE INDEX idx_extracted_inspection ON extracted_fields(inspection_id);
```

### compliance_checks

```sql
CREATE TABLE compliance_checks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    inspection_id TEXT NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    check_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PASS', 'FAIL', 'REVIEW', 'N/A')),
    severity TEXT NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    detected_value TEXT,
    expected_value TEXT,
    confidence REAL,
    reason TEXT,
    evidence_json TEXT,
    legal_citation TEXT,
    legal_page INTEGER,
    legal_text TEXT,
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_checks_inspection ON compliance_checks(inspection_id);
CREATE INDEX idx_checks_status ON compliance_checks(status);
```

### review_actions

```sql
CREATE TABLE review_actions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    check_record_id TEXT NOT NULL REFERENCES compliance_checks(id) ON DELETE CASCADE,
    inspection_id TEXT NOT NULL REFERENCES inspections(id),
    reviewer_id TEXT NOT NULL REFERENCES users(id),
    original_status TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('OVERRIDE_TO_PASS', 'OVERRIDE_TO_FAIL', 'CONFIRM_REVIEW', 'CORRECT_VALUE')),
    corrected_value TEXT,
    notes TEXT,
    final_status TEXT NOT NULL,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_reviews_inspection ON review_actions(inspection_id);
```

### legal_chunks

```sql
CREATE TABLE legal_chunks (
    id TEXT PRIMARY KEY,
    document_name TEXT NOT NULL,
    document_title TEXT NOT NULL,
    rule_number TEXT,
    sub_rule TEXT,
    clause TEXT,
    chapter TEXT,
    page_number INTEGER,
    section_title TEXT,
    chunk_type TEXT CHECK (chunk_type IN ('rule', 'schedule', 'definition', 'proviso', 'explanation', 'penalty', 'general')),
    text TEXT NOT NULL,
    embedding_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_chunks_rule ON legal_chunks(rule_number);
CREATE INDEX idx_chunks_document ON legal_chunks(document_name);
```

---

# 12. API Contract

## 12.1 Base URL

```
http://localhost:8000/api/v1
```

## 12.2 Endpoints

### POST /auth/login

**Purpose:** User authentication  
**Request:**
```json
{
  "username": "inspector1",
  "password": "password123"
}
```
**Response (200):**
```json
{
  "token": "jwt_token_here",
  "user": {
    "id": "uuid",
    "username": "inspector1",
    "full_name": "Inspector Singh",
    "role": "inspector"
  }
}
```

---

### POST /inspections

**Purpose:** Create new inspection and upload image  
**Request:** `multipart/form-data`
- `image`: file (JPEG/PNG, max 10MB)
- `category_hint`: string (optional: "food", "cosmetics", "household", "general", "unknown")
- `notes`: string (optional)

**Response (201):**
```json
{
  "inspection_id": "uuid",
  "status": "PENDING",
  "message": "Inspection created. Processing..."
}
```

---

### POST /inspections/{id}/analyze

**Purpose:** Trigger the full analysis pipeline (OCR + RAG + Compliance)  
**Request:** Empty body (or optional overrides)  
**Response (200):**
```json
{
  "inspection_id": "uuid",
  "overall_status": "FAIL",
  "compliance_score": 75.0,
  "summary": {
    "total_checks": 8,
    "passed": 6,
    "failed": 1,
    "review": 1
  },
  "checks": [ /* array of check results per Section 8.3 */ ],
  "disclaimers": [ /* array of disclaimer strings */ ]
}
```

**Error (422):**
```json
{
  "error": "image_quality_too_low",
  "message": "Image quality is too low for reliable OCR extraction. Please upload a clearer image.",
  "ocr_confidence": 0.3
}
```

---

### GET /inspections/{id}

**Purpose:** Get full inspection details  
**Response (200):** Full inspection object with all checks, extracted fields, and review actions.

---

### GET /inspections

**Purpose:** List all inspections (with pagination and filters)  
**Query Parameters:**
- `page` (default 1)
- `per_page` (default 20)
- `status` (optional: PASS, FAIL, REVIEW)
- `date_from` (optional: ISO date)
- `date_to` (optional: ISO date)

**Response (200):**
```json
{
  "inspections": [ /* array of inspection summaries */ ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3
  }
}
```

---

### GET /inspections/{id}/report

**Purpose:** Generate and return an inspection report  
**Query Parameters:**
- `format`: "html" (default) or "pdf"

**Response (200):** HTML or PDF report.

---

### POST /inspections/{id}/review

**Purpose:** Submit a human review action for a specific check  
**Request:**
```json
{
  "check_id": "CHK-06",
  "action": "OVERRIDE_TO_PASS",
  "corrected_value": "1800-123-4567",
  "notes": "Consumer care number visible on back panel."
}
```

**Response (200):**
```json
{
  "review_id": "uuid",
  "final_status": "PASS",
  "message": "Review action saved."
}
```

---

### GET /dashboard

**Purpose:** Get dashboard analytics  
**Response (200):**
```json
{
  "total_inspections": 45,
  "status_distribution": {
    "PASS": 20,
    "FAIL": 15,
    "REVIEW": 10
  },
  "common_violations": [
    {"check_id": "CHK-06", "rule_name": "Consumer Care Info", "count": 12},
    {"check_id": "CHK-03", "rule_name": "MRP Declaration", "count": 8}
  ],
  "recent_inspections": [ /* last 5 */ ],
  "daily_counts": [ /* last 30 days */ ]
}
```

---

### GET /legal/search

**Purpose:** Search legal corpus (RAG)  
**Query Parameters:**
- `q`: search query string
- `top_k`: number of results (default 5)

**Response (200):**
```json
{
  "results": [ /* array of legal chunks with metadata */ ]
}
```

---

### GET /inspections/{id}/evidence/{check_id}/image

**Purpose:** Get annotated image region for a specific check's evidence  
**Response (200):** Image file (PNG) with highlighted bounding box.

---

# 13. Frontend Specification

## 13.1 Technology

- **Framework:** React (created with Vite)
- **Styling:** Vanilla CSS with CSS custom properties (design tokens)
- **State Management:** React Context + useReducer (no Redux needed)
- **HTTP:** fetch API or Axios
- **Charts:** Chart.js or Recharts
- **Routing:** React Router v6

## 13.2 Design System

```css
:root {
  /* Colors */
  --color-bg: #0f1117;
  --color-surface: #1a1d27;
  --color-surface-elevated: #242836;
  --color-primary: #6366f1;
  --color-primary-light: #818cf8;
  --color-success: #10b981;
  --color-danger: #ef4444;
  --color-warning: #f59e0b;
  --color-info: #3b82f6;
  --color-text: #e2e8f0;
  --color-text-muted: #94a3b8;
  
  /* Status colors */
  --color-pass: #10b981;
  --color-fail: #ef4444;
  --color-review: #f59e0b;
  
  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
  
  /* Border radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  
  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.5);
}
```

## 13.3 Screens

### Screen 1: Login

**Purpose:** Authentication  
**Components:** Logo, login form (username + password), submit button  
**API:** POST /auth/login  
**States:** Loading, error (invalid credentials), success (redirect to dashboard)

### Screen 2: Dashboard

**Purpose:** Overview of all inspections and analytics  
**Components:**
- Summary cards (total inspections, PASS/FAIL/REVIEW counts)
- Chart: status distribution (pie/donut)
- Chart: inspections over time (line/bar)
- Top violations table
- Recent inspections list with status badges
- "New Inspection" button (prominent CTA)

**API:** GET /dashboard, GET /inspections  
**States:** Loading skeleton, empty state, populated

### Screen 3: New Inspection / Upload

**Purpose:** Upload or capture a product image  
**Components:**
- Drag-and-drop upload zone
- Camera capture button (uses browser MediaDevices API)
- Image preview
- Optional: category selector dropdown
- Optional: notes text area
- "Analyze" button

**API:** POST /inspections  
**States:** Idle, image selected (preview), uploading, processing (animated progress)

### Screen 4: Processing / Scanning

**Purpose:** Show progress while analysis runs  
**Components:**
- Animated progress indicator
- Step indicators: "Extracting text..." → "Retrieving legal context..." → "Running compliance checks..." → "Generating report..."
- Image thumbnail

**API:** POST /inspections/{id}/analyze (called automatically after upload)  
**States:** Processing steps (animated), complete (auto-redirect to results)

### Screen 5: Compliance Results (HERO SCREEN)

**Purpose:** Display the compliance analysis results  
**Components:**
- Overall status badge (large: PASS/FAIL/REVIEW with color)
- Compliance score gauge (circular)
- Summary bar (X passed, Y failed, Z review)
- Check results list:
  - Each check: status icon, rule name, detected value, severity badge
  - Expandable: shows full details, evidence, legal citation, recommendation
- Image viewer with annotated bounding boxes
- "Generate Report" button
- "Review" buttons for REVIEW items

**API:** GET /inspections/{id}  
**States:** Loading, results displayed  
**UX:** This is the most important screen. It must be visually stunning with clear status indicators.

### Screen 6: Violation / Check Detail

**Purpose:** Deep dive into a single compliance check  
**Components:**
- Check status badge
- Detected value (highlighted)
- Expected value (per rule)
- Confidence meter
- Evidence: image region with bounding box
- Legal source: rule citation, rule text, page number
- Explanation text
- Recommendation
- Review action buttons (if status is REVIEW)

**API:** Part of GET /inspections/{id}  
**States:** Viewing, reviewing (form visible)

### Screen 7: Report View

**Purpose:** Display the generated inspection report  
**Components:**
- Formatted report with header (date, inspector, product)
- Overall result
- Each check result
- Legal citations
- Evidence images
- Disclaimers
- Print/Download buttons

**API:** GET /inspections/{id}/report  
**States:** Loading, displayed

### Screen 8: Inspection History

**Purpose:** Browse past inspections  
**Components:**
- Filterable table: date, product, status, score
- Status filter tabs (All, PASS, FAIL, REVIEW)
- Search bar
- Pagination

**API:** GET /inspections  

---

# 14. Repository Structure

```
SIH_PS34/
|
|-- legal_docs/                     # Source legal documents
|   |-- rules2009.pdf
|   |-- rules2011.pdf
|
|-- RULE_MATRIX.md                  # Regulatory rule matrix (this spec)
|-- MASTER_BUILD_SPEC.md            # This document
|
|-- backend/
|   |-- requirements.txt            # Python dependencies
|   |-- main.py                     # FastAPI application entry point
|   |-- config.py                   # Configuration (API keys, paths, etc.)
|   |-- database.py                 # Database connection and initialization
|   |-- models.py                   # SQLAlchemy/Pydantic models
|   |-- schemas.py                  # Pydantic request/response schemas
|   |
|   |-- api/
|   |   |-- __init__.py
|   |   |-- auth.py                 # Authentication endpoints
|   |   |-- inspections.py          # Inspection CRUD and analysis endpoints
|   |   |-- dashboard.py            # Dashboard analytics endpoint
|   |   |-- legal.py                # Legal corpus search endpoint
|   |   |-- reports.py              # Report generation endpoint
|   |
|   |-- ocr/
|   |   |-- __init__.py
|   |   |-- pipeline.py             # OCR orchestration
|   |   |-- preprocessing.py        # Image preprocessing (resize, enhance, deskew)
|   |   |-- extractor.py            # Field extraction (LLM-assisted structuring)
|   |   |-- schemas.py              # OCR output schemas (Section 7.2)
|   |
|   |-- rag/
|   |   |-- __init__.py
|   |   |-- ingest.py               # PDF ingestion and chunking
|   |   |-- embeddings.py           # Embedding generation
|   |   |-- store.py                # ChromaDB operations
|   |   |-- retriever.py            # Query construction and retrieval
|   |   |-- schemas.py              # RAG data models
|   |
|   |-- compliance/
|   |   |-- __init__.py
|   |   |-- engine.py               # Main compliance engine
|   |   |-- rules.py                # Individual rule validators (CHK-01 through CHK-10)
|   |   |-- schemas.py              # Compliance input/output schemas (Section 8)
|   |   |-- scoring.py              # Score calculation
|   |   |-- explainer.py            # Explanation generation
|   |
|   |-- evidence/
|   |   |-- __init__.py
|   |   |-- annotator.py            # Image annotation with bounding boxes
|   |   |-- report_generator.py     # HTML/PDF report generation
|   |
|   |-- data/
|   |   |-- chroma_db/              # ChromaDB persistent storage
|   |   |-- uploads/                # Uploaded images
|   |   |-- annotated/              # Annotated images
|   |   |-- reports/                # Generated reports
|   |   |-- database.db             # SQLite database file
|
|-- frontend/
|   |-- package.json
|   |-- vite.config.js
|   |-- index.html
|   |-- public/
|   |   |-- favicon.ico
|   |
|   |-- src/
|   |   |-- main.jsx                # App entry
|   |   |-- App.jsx                 # Router setup
|   |   |-- index.css               # Global styles and design tokens
|   |   |
|   |   |-- components/
|   |   |   |-- Layout.jsx          # App shell (sidebar, header)
|   |   |   |-- StatusBadge.jsx     # PASS/FAIL/REVIEW badge
|   |   |   |-- ComplianceGauge.jsx # Circular score gauge
|   |   |   |-- CheckCard.jsx       # Individual check result card
|   |   |   |-- ImageViewer.jsx     # Image with bounding box overlays
|   |   |   |-- UploadZone.jsx      # Drag-and-drop upload
|   |   |   |-- ReviewForm.jsx      # Human review form
|   |   |   |-- LegalCitation.jsx   # Legal source display
|   |   |   |-- LoadingSkeleton.jsx # Loading states
|   |   |
|   |   |-- pages/
|   |   |   |-- Login.jsx
|   |   |   |-- Dashboard.jsx
|   |   |   |-- NewInspection.jsx
|   |   |   |-- InspectionResults.jsx  # HERO SCREEN
|   |   |   |-- InspectionHistory.jsx
|   |   |   |-- ReportView.jsx
|   |   |
|   |   |-- api/
|   |   |   |-- client.js           # API client (fetch wrapper)
|   |   |
|   |   |-- context/
|   |   |   |-- AuthContext.jsx     # Auth state
|
|-- tests/
|   |-- test_compliance_engine.py   # Compliance rule unit tests
|   |-- test_ocr_extraction.py      # OCR schema validation tests
|   |-- test_rag_retrieval.py       # RAG retrieval tests
|   |-- test_api.py                 # API endpoint tests
|   |-- golden_test_data/           # Golden test inputs and expected outputs
|   |   |-- test_001_compliant.json
|   |   |-- test_002_missing_mrp.json
|   |   |-- ...
|
|-- demo/
|   |-- sample_images/              # Demo product images
|   |-- demo_script.md              # Demo talking points
```

**File ownership:**

| Directory | Owner (Person) |
|---|---|
| `frontend/src/pages/Login.jsx`, `NewInspection.jsx`, `Layout.jsx`, `UploadZone.jsx` | Person 1 |
| `frontend/src/pages/InspectionResults.jsx`, `Dashboard.jsx`, `ReportView.jsx`, `InspectionHistory.jsx` + result components | Person 2 |
| `backend/api/`, `backend/main.py`, `backend/schemas.py` | Person 3 |
| `backend/database.py`, `backend/models.py`, integration, deployment | Person 4 |
| `backend/ocr/`, `backend/evidence/annotator.py` | Person 5 |
| `backend/compliance/`, `backend/rag/`, `tests/`, `demo/` | Person 6 |

---

# 15. Team Responsibilities

## Person 1: Frontend — Application Shell

**Scope:** Login, layout, navigation, upload/capture screen, processing screen  
**Files:**
- `frontend/src/App.jsx`
- `frontend/src/index.css`
- `frontend/src/pages/Login.jsx`
- `frontend/src/pages/NewInspection.jsx`
- `frontend/src/components/Layout.jsx`
- `frontend/src/components/UploadZone.jsx`
- `frontend/src/components/LoadingSkeleton.jsx`
- `frontend/src/api/client.js`
- `frontend/src/context/AuthContext.jsx`

**Interfaces consumed:**
- POST /auth/login
- POST /inspections
- POST /inspections/{id}/analyze

**Delivers:** Working login, image upload with preview, processing animation

---

## Person 2: Frontend — Results, Dashboard, Reports

**Scope:** Compliance results (hero screen), dashboard, inspection history, report view, review form  
**Files:**
- `frontend/src/pages/InspectionResults.jsx`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/InspectionHistory.jsx`
- `frontend/src/pages/ReportView.jsx`
- `frontend/src/components/StatusBadge.jsx`
- `frontend/src/components/ComplianceGauge.jsx`
- `frontend/src/components/CheckCard.jsx`
- `frontend/src/components/ImageViewer.jsx`
- `frontend/src/components/ReviewForm.jsx`
- `frontend/src/components/LegalCitation.jsx`

**Interfaces consumed:**
- GET /inspections/{id}
- GET /inspections
- GET /dashboard
- GET /inspections/{id}/report
- POST /inspections/{id}/review
- GET /inspections/{id}/evidence/{check_id}/image

**Delivers:** Stunning results page, functional dashboard with charts, report viewer

---

## Person 3: Backend — API Layer

**Scope:** All API endpoints, request validation, response formatting, error handling, CORS, middleware  
**Files:**
- `backend/main.py`
- `backend/config.py`
- `backend/schemas.py`
- `backend/api/auth.py`
- `backend/api/inspections.py`
- `backend/api/dashboard.py`
- `backend/api/legal.py`
- `backend/api/reports.py`

**Interfaces provided:** All endpoints defined in Section 12  
**Interfaces consumed:** Calls OCR pipeline, compliance engine, RAG retriever, database

**Delivers:** Fully functional API that frontend can call. Validated request/response schemas.

---

## Person 4: Database and Integration

**Scope:** Database setup, migrations, data access layer, deployment, CI/CD, CORS config, environment setup  
**Files:**
- `backend/database.py`
- `backend/models.py`
- `backend/requirements.txt`
- Database initialization scripts
- `.env.example`
- `docker-compose.yml` (if needed)
- Integration testing

**Delivers:** Working database, data access functions, deployment configuration, environment setup documentation

---

## Person 5: OCR and Image Processing

**Scope:** Image preprocessing, OCR integration, structured field extraction, image annotation  
**Files:**
- `backend/ocr/__init__.py`
- `backend/ocr/pipeline.py`
- `backend/ocr/preprocessing.py`
- `backend/ocr/extractor.py`
- `backend/ocr/schemas.py`
- `backend/evidence/annotator.py`

**Interfaces provided:** OCR output schema (Section 7.2) — this is the contract between OCR and Compliance Engine  
**Interfaces consumed:** Google Cloud Vision API or Tesseract; Gemini API for LLM-assisted extraction

**Delivers:** Given an image, returns structured product facts in the exact schema defined in Section 7.2. Also generates annotated images with bounding boxes.

---

## Person 6: Compliance Engine, RAG, Rules, Testing, Demo Data

**Scope:** This is the most architecturally important role. Connects legal documents to compliance decisions.  
**Files:**
- `backend/rag/ingest.py`
- `backend/rag/embeddings.py`
- `backend/rag/store.py`
- `backend/rag/retriever.py`
- `backend/rag/schemas.py`
- `backend/compliance/engine.py`
- `backend/compliance/rules.py`
- `backend/compliance/schemas.py`
- `backend/compliance/scoring.py`
- `backend/compliance/explainer.py`
- `backend/evidence/report_generator.py`
- `tests/test_compliance_engine.py`
- `tests/golden_test_data/`
- `demo/sample_images/`
- `demo/demo_script.md`

**Interfaces provided:**
- Compliance engine input/output (Section 8)
- RAG retrieval results (Section 6)
- Report generation

**Interfaces consumed:**
- OCR output (Section 7.2 — from Person 5)
- Database (from Person 4)

**Delivers:** Working RAG pipeline, compliance engine that passes all golden tests, report generator, demo dataset, test suite.

---

## Interface Contract Summary

```
Person 1 (FE Shell) --[API calls]--> Person 3 (Backend API)
Person 2 (FE Results) --[API calls]--> Person 3 (Backend API)
Person 3 (Backend API) --[calls]--> Person 5 (OCR Pipeline)
Person 3 (Backend API) --[calls]--> Person 6 (Compliance Engine)
Person 3 (Backend API) --[calls]--> Person 4 (Database)
Person 5 (OCR) --[delivers OCR facts]--> Person 6 (Compliance Engine)
Person 6 (Compliance) --[uses]--> Person 6 (RAG)
Person 6 (Compliance) --[stores results]--> Person 4 (Database)
```

**CRITICAL:** Person 5 and Person 6 MUST agree on the OCR output schema (Section 7.2) by end of Day 1. This is the most important interface in the system.

---

# 16. Demo Dataset

## 16.1 Test Cases

### TEST-001: Fully Compliant Product

**Product:** Common biscuit package (Indian brand)  
**Expected OCR fields:** All fields present  
**Expected result:** PASS (all checks pass)  
**Expected violations:** None  
**Expected score:** 100  
**Purpose:** Prove the system can recognize a compliant product

### TEST-002: Missing MRP

**Product:** Package image with MRP obscured or absent  
**Expected OCR fields:** MRP is null  
**Expected result:** FAIL  
**Expected violations:** CHK-03 (MRP Declaration) — FAIL, CRITICAL  
**Expected explanation:** "Rule 6(1)(e) requires declaration of retail sale price..."  
**Purpose:** Demonstrate high-severity violation detection

### TEST-003: Missing Consumer Care Information

**Product:** Package without visible phone/email for complaints  
**Expected OCR fields:** consumer_care is null  
**Expected result:** FAIL  
**Expected violations:** CHK-06 (Consumer Care) — FAIL, HIGH  
**Purpose:** Demonstrate contact info requirement

### TEST-004: Missing Net Quantity

**Product:** Package without visible net quantity declaration  
**Expected OCR fields:** net_quantity is null  
**Expected result:** FAIL  
**Expected violations:** CHK-02 (Net Quantity) — FAIL, CRITICAL  
**Purpose:** Demonstrate quantity requirement

### TEST-005: Missing Manufacturer/Packer Information

**Product:** Package without visible manufacturer details  
**Expected OCR fields:** manufacturer, packer, importer all null  
**Expected result:** FAIL  
**Expected violations:** CHK-04 — FAIL, CRITICAL  
**Purpose:** Demonstrate entity identification requirement

### TEST-006: Multiple Violations

**Product:** Package missing MRP + consumer care + manufacturing date  
**Expected result:** FAIL  
**Expected violations:** CHK-03, CHK-05, CHK-06  
**Expected score:** ~40  
**Purpose:** Demonstrate multi-violation handling

### TEST-007: Low Quality / Uncertain Image

**Product:** Blurry or angled photo of a package  
**Expected OCR fields:** Some fields with very low confidence  
**Expected result:** REVIEW  
**Expected violations:** Multiple checks with REVIEW status  
**Purpose:** Demonstrate REVIEW workflow and human-in-the-loop

### TEST-008: Imported Product — Missing Country of Origin

**Product:** Product with "Imported by" text but no "Country of Origin"  
**Expected OCR fields:** importer present, country_of_origin null  
**Expected result:** FAIL  
**Expected violations:** CHK-09 (Country of Origin) — FAIL, HIGH  
**Purpose:** Demonstrate conditional rule checking

### TEST-009: MRP Without Tax Declaration

**Product:** Package with "MRP Rs. 50" but without "inclusive of all taxes"  
**Expected OCR fields:** MRP amount found but includes_tax is false  
**Expected result:** FAIL  
**Expected violations:** CHK-03 — FAIL (format violation)  
**Purpose:** Demonstrate format compliance beyond mere presence

### TEST-010: Misleading Quantity Qualifier

**Product:** Package with "Approx. 500g" or "Minimum 250ml"  
**Expected OCR fields:** quantity_qualifiers_detected contains "approx" or "minimum"  
**Expected result:** FAIL  
**Expected violations:** CHK-07 — FAIL  
**Purpose:** Demonstrate keyword-based rule checking

## 16.2 Demo Data Structure

Each test case is a JSON file in `tests/golden_test_data/`:

```json
{
  "test_id": "TEST-001",
  "description": "Fully compliant biscuit package",
  "image_path": "demo/sample_images/compliant_biscuit.jpg",
  "mock_ocr_output": { /* Section 7.2 schema */ },
  "expected_overall_status": "PASS",
  "expected_check_results": {
    "CHK-01": "PASS",
    "CHK-02": "PASS",
    "CHK-03": "PASS",
    "CHK-04": "PASS",
    "CHK-05": "PASS",
    "CHK-06": "PASS",
    "CHK-07": "PASS",
    "CHK-09": "N/A"
  },
  "expected_score_range": [95, 100]
}
```

## 16.3 Fallback for Demo

If OCR is unreliable for a specific demo image, the system can use a **mock OCR mode** where pre-extracted facts are loaded from the golden test data. This is architecturally honest because:
1. The OCR pipeline still processes the image
2. The mock data has the same schema as real OCR output
3. The compliance engine operates identically
4. The judge can be told: "For demo reliability, we have a fallback mode. In production, this uses live OCR."

---

# 17. Testing Strategy

## 17.1 Unit Tests — Compliance Rules

File: `tests/test_compliance_engine.py`

```python
# Test each rule validator independently with mock OCR data

def test_chk01_pass():
    """Product name is present with high confidence"""
    ocr_facts = {"fields": {"product_name": {"value": "Biscuits", "confidence": 0.9}}}
    result = check_product_name(ocr_facts)
    assert result["status"] == "PASS"

def test_chk01_fail():
    """Product name is absent with high overall confidence"""
    ocr_facts = {"overall_confidence": 0.85, "fields": {"product_name": {"value": None, "confidence": None}}}
    result = check_product_name(ocr_facts)
    assert result["status"] == "FAIL"

def test_chk01_review():
    """Product name is absent with low overall confidence"""
    ocr_facts = {"overall_confidence": 0.5, "fields": {"product_name": {"value": None, "confidence": None}}}
    result = check_product_name(ocr_facts)
    assert result["status"] == "REVIEW"

# Similar tests for CHK-02 through CHK-10
# ~30 test cases total
```

## 17.2 RAG Retrieval Tests

File: `tests/test_rag_retrieval.py`

```python
def test_rag_returns_rule6_for_mrp_query():
    """Querying for MRP should return Rule 6(1)(e) and Rule 2(m)"""
    results = retriever.query("maximum retail price MRP declaration")
    rule_numbers = [r["metadata"]["rule"] for r in results]
    assert "6" in rule_numbers or "2" in rule_numbers

def test_rag_returns_correct_page():
    """Retrieved chunks should have correct page numbers"""
    results = retriever.query("net quantity declaration")
    for r in results:
        assert r["metadata"]["page"] is not None
        assert isinstance(r["metadata"]["page"], int)
```

## 17.3 Golden Test Set

Run all 10 golden test cases through the compliance engine with mock OCR data:

```bash
python -m pytest tests/test_compliance_engine.py -v
```

Expected results:

| Test | Expected | What It Validates |
|---|---|---|
| TEST-001 | PASS, score 100 | All checks pass |
| TEST-002 | FAIL, CHK-03 fails | MRP detection |
| TEST-003 | FAIL, CHK-06 fails | Consumer care detection |
| TEST-004 | FAIL, CHK-02 fails | Net quantity detection |
| TEST-005 | FAIL, CHK-04 fails | Manufacturer detection |
| TEST-006 | FAIL, 3 failures | Multi-violation |
| TEST-007 | REVIEW | Low confidence handling |
| TEST-008 | FAIL, CHK-09 fails | Conditional rule |
| TEST-009 | FAIL, CHK-03 fails | Format validation |
| TEST-010 | FAIL, CHK-07 fails | Keyword detection |

## 17.4 API Tests

File: `tests/test_api.py`

```python
def test_create_inspection():
    response = client.post("/api/v1/inspections", files={"image": test_image})
    assert response.status_code == 201

def test_analyze_inspection():
    response = client.post(f"/api/v1/inspections/{inspection_id}/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] in ["PASS", "FAIL", "REVIEW"]
```

---

# 18. Five-Day Development Plan

## Day 1: Foundation

**Objectives:** Project structure, legal analysis complete, interfaces defined, RAG pipeline operational

**Deliverables:**
- [ ] Repository structure created (all folders and placeholder files)
- [ ] `requirements.txt` finalized
- [ ] Database schema implemented and migrations run
- [ ] OCR output schema (Section 7.2) agreed upon and documented
- [ ] Compliance output schema (Section 8.3) agreed upon and documented
- [ ] RAG pipeline: PDF ingestion, chunking, embedding, ChromaDB storage
- [ ] RAG pipeline: Basic retrieval working (can query and get relevant rules)
- [ ] Frontend: Vite project initialized, routing set up, design tokens defined
- [ ] Authentication: Basic JWT auth implemented

**Dependencies:** None (Day 1 is parallel work)

**Must NOT attempt:**
- Full compliance engine logic
- Full frontend screens
- Deployment

---

## Day 2: Core Pipelines

**Objectives:** OCR pipeline working, basic compliance engine, frontend shell

**Deliverables:**
- [ ] OCR pipeline: Image preprocessing + Google Cloud Vision API integration
- [ ] OCR pipeline: LLM-assisted field extraction producing Section 7.2 schema
- [ ] Compliance engine: CHK-01 through CHK-04 (the 4 CRITICAL checks) implemented
- [ ] Compliance engine: Status determination logic (PASS/FAIL/REVIEW)
- [ ] Backend API: POST /inspections, POST /inspections/{id}/analyze endpoints
- [ ] Frontend: Login page, Layout/shell, Upload page with image preview
- [ ] Database: CRUD operations for inspections

**Dependencies:**
- OCR schema must be finalized (from Day 1)
- Database must be running (from Day 1)

**Must NOT attempt:**
- Report generation
- Dashboard analytics
- Image annotation

---

## Day 3: End-to-End Integration

**Objectives:** Complete pipeline from image upload to compliance results

**Deliverables:**
- [ ] Compliance engine: CHK-05 through CHK-07, CHK-09 implemented (all 8 MVP rules)
- [ ] RAG integration: Compliance engine retrieves legal context for each check
- [ ] Evidence: Bounding box annotations on images
- [ ] Backend: Complete analysis pipeline (upload to result to save to DB)
- [ ] Frontend: Compliance Results page (hero screen) — overall status, check cards, evidence
- [ ] End-to-end test: Upload image and see results in browser
- [ ] Golden test set: At least TEST-001, TEST-002, TEST-003 passing

**Dependencies:**
- OCR pipeline working (from Day 2)
- Compliance engine CRITICAL checks (from Day 2)
- API endpoints (from Day 2)

**Must NOT attempt:**
- Polish and animations
- Report PDF generation
- Complex dashboard charts

---

## Day 4: Features and Polish

**Objectives:** Dashboard, reports, human review, visual polish

**Deliverables:**
- [ ] Dashboard: Analytics endpoint and frontend page with charts
- [ ] Report generation: HTML report with compliance summary, evidence, citations
- [ ] Human review: Review endpoint and ReviewForm component
- [ ] Inspection history: List page with filters
- [ ] Frontend: Visual polish — animations, transitions, loading states
- [ ] Frontend: Responsive design verification
- [ ] Compliance engine: Explainability improvements (better explanation text)
- [ ] Legal citation: Full source text displayed in results

**Dependencies:**
- End-to-end pipeline working (from Day 3)

**Must NOT attempt:**
- PDF report generation (HTML is sufficient)
- Mobile optimization beyond responsive
- New features not in the spec

---

## Day 5: Testing, Demo, Deployment

**Objectives:** All tests passing, demo rehearsed, system deployed

**Deliverables:**
- [ ] All 10 golden test cases passing
- [ ] Unit tests passing (compliance engine)
- [ ] RAG retrieval tests passing
- [ ] API tests passing
- [ ] Demo dataset: All 10 test images prepared
- [ ] Demo script: Rehearsed 2-3 minute demo path
- [ ] Mock/fallback mode: Working for demo reliability
- [ ] Bug fixes: Critical issues resolved
- [ ] Deployment: Running on a single machine (localhost or simple deploy)
- [ ] Final walkthrough: Every screen works as expected

**Dependencies:**
- Everything from Days 1-4

**Must NOT attempt:**
- New features
- Architecture changes
- Cloud deployment (unless already set up)

---

# 19. Demo Flow

## 2-3 Minute Judge Demonstration Script

### Scene 1: Login (10 seconds)
- Show the login screen
- Log in as "Inspector Singh"
- Brief: "This is our AI-assisted compliance assessment platform."

### Scene 2: Dashboard (15 seconds)
- Show the dashboard with existing inspections
- Point out: "We've already analyzed 45 packages. Here are the common violations..."
- Show status distribution chart
- Click "New Inspection"

### Scene 3: Upload (15 seconds)
- Upload a pre-selected product image (TEST-006: multiple violations)
- Show image preview
- Click "Analyze"

### Scene 4: Processing (10 seconds)
- Show the animated processing steps
- Brief: "The system is now extracting text, retrieving legal context, and running compliance checks..."

### Scene 5: Results (45 seconds — THE HERO MOMENT)
- Show the big FAIL badge with compliance score
- Walk through each check:
  - "Product name: PASS"
  - "Net Quantity: PASS"
  - "MRP: FAIL — the MRP is present but missing 'inclusive of all taxes'"
  - "Consumer Care: FAIL — no contact information detected"
- Click on a FAIL check to expand it

### Scene 6: Evidence and Legal Source (30 seconds)
- Show the expanded violation detail
- Point to: "Here's the detected text... here's what the rule requires..."
- Show the legal citation: "Rule 6(1)(e), Rule 2(m), page 3 of the Legal Metrology Rules, 2011"
- Show the image with highlighted bounding boxes

### Scene 7: Manual Review (15 seconds)
- Show a REVIEW item
- Demonstrate the review form
- Override the result
- Brief: "Inspectors can review uncertain findings and make corrections"

### Scene 8: Generate Report (10 seconds)
- Click "Generate Report"
- Show the formatted report
- Brief: "The system generates an inspection-ready report with full legal citations"

### Scene 9: Close (10 seconds)
- Return to dashboard
- Brief: "All inspections are saved for audit trails and analytics"
- "This is an AI-assisted preliminary assessment — always paired with human review"

### Total: ~2.5 minutes

### Fallback Strategy:
- Use TEST-006 (multiple violations) as the primary demo — it demonstrates the most features
- Use pre-extracted mock OCR data for reliability
- If live OCR is working well, use a real clear product image
- Keep TEST-001 (fully compliant) ready as a backup demo

---

# 20. MVP vs Future Scope

## MUST HAVE FOR DEMO

| Feature | Status |
|---|---|
| Image upload and preview | Required |
| OCR text extraction | Required |
| Structured field extraction (8+ fields) | Required |
| RAG-indexed legal corpus (2 PDFs) | Required |
| 8 MVP compliance rules (CHK-01 to CHK-07, CHK-09) | Required |
| PASS / FAIL / REVIEW results | Required |
| Per-check explanation with legal citation | Required |
| Evidence with bounding boxes | Required |
| Basic dashboard with status counts | Required |
| Report generation (HTML) | Required |
| Human review workflow | Required |
| Inspection history | Required |
| Login screen | Required |

## SHOULD HAVE IF TIME REMAINS

| Feature | Priority |
|---|---|
| CHK-08 (Language compliance) | Medium |
| CHK-10 (MRP sticker check) | Medium |
| PDF report export | Medium |
| Improved OCR preprocessing | Medium |
| Better dashboard charts | Low |
| Dark/light theme toggle | Low |

## FUTURE SCOPE

| Feature | Why Deferred |
|---|---|
| Mobile native app | Time constraint |
| Real-time video scanning | Complexity |
| Barcode/QR code lookup | Additional API integration |
| Custom ML model for label detection | Training data needed |
| Font size compliance (Rule 7) | Requires real-world measurement |
| Color contrast analysis (Rule 9) | Requires advanced CV |
| Standard pack size validation (Rule 5) | Requires category identification |
| FSSAI integration | Out of scope for 2011 Rules |
| Multilingual OCR (beyond Hindi/English) | Complexity |
| Cloud deployment (AWS/GCP) | Not needed for demo |
| Microservices architecture | Over-engineering for prototype |
| Complex authentication (OAuth, RBAC) | Simple JWT sufficient |
| Batch scanning of multiple products | Single-product flow is sufficient |
| Integration with Legal Metrology Department databases | Not available |

---

# 21. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OCR accuracy is poor on real product images | HIGH | HIGH | Use mock OCR data for demo; pre-process images; use Google Cloud Vision API |
| LLM (Gemini) is slow or unavailable | MEDIUM | HIGH | Cache extraction results; have fallback extraction logic; timeout handling |
| Team member unavailable | LOW | HIGH | Cross-train on interfaces; documented schemas allow handoff |
| ChromaDB issues | LOW | MEDIUM | Fallback to simple keyword search on legal text |
| Image upload is too slow | LOW | MEDIUM | Client-side compression; progress indicators |
| Legal interpretation is incorrect | MEDIUM | MEDIUM | All rules traced to source; system presents as "preliminary assessment" |
| Demo image does not produce expected results | MEDIUM | HIGH | Use golden test dataset with mock OCR mode |
| Frontend-backend integration issues | MEDIUM | MEDIUM | Agree on schemas Day 1; use mock API responses for parallel development |

---

# 22. Coding Agent Instructions

## 22.1 Universal Rules for All Agents

1. **NEVER** invent a different architecture. Follow this specification exactly.
2. **NEVER** change the OCR output schema (Section 7.2) without updating all consumers.
3. **NEVER** change the compliance output schema (Section 8.3) without updating all consumers.
4. **ALWAYS** use the exact field names defined in the schemas.
5. **ALWAYS** use `null` for missing values, not "N/A", "not found", empty strings, or sentinel values.
6. **ALWAYS** include legal citations from RULE_MATRIX.md for every compliance check.
7. **NEVER** use an LLM to make final PASS/FAIL compliance decisions. Use deterministic logic.
8. **ALWAYS** include confidence scores in OCR output and compliance results.
9. **ALWAYS** include disclaimers that this is a preliminary assessment.
10. **FOLLOW** the repository structure defined in Section 14.

## 22.2 Agent Task: RAG Pipeline (Person 6)

**File:** `backend/rag/ingest.py`  
**Purpose:** Ingest rules2009.pdf and rules2011.pdf, chunk them by rule, generate embeddings, store in ChromaDB  
**Dependencies:** PyMuPDF, sentence-transformers, chromadb  
**Input:** PDF files in `legal_docs/`  
**Output:** Populated ChromaDB collection with chunks and metadata  
**Interface that must not change:** Chunk metadata format (Section 6.6)  
**Implementation requirements:**
- Use PyMuPDF to extract text page by page
- Split by rule number using regex
- Each chunk gets metadata: document, rule, sub_rule, page, chapter, chunk_type
- Use `all-MiniLM-L6-v2` for embeddings
- Store in ChromaDB with persistent storage in `backend/data/chroma_db/`
- Log number of chunks created per document

**Acceptance criteria:**
- Running `python -m backend.rag.ingest` creates a ChromaDB collection
- Querying "MRP retail sale price" returns chunks containing Rule 6(1)(e) and Rule 2(m)
- Each chunk has complete metadata (no null fields except sub_rule which may be null for top-level rules)

**Edge cases:**
- Table formatting in PDFs — tables may be garbled by text extraction. Accept imperfect tables but log warnings.
- Schedule text — may contain column data that doesn't parse well. Chunk as-is with schedule type.

---

**File:** `backend/rag/retriever.py`  
**Purpose:** Query ChromaDB and return relevant legal chunks  
**Dependencies:** chromadb  
**Input:** Query string + optional metadata filters  
**Output:** List of chunks with metadata and similarity scores (Section 6.6 format)  
**Interface that must not change:** Retrieval result format  
**Implementation requirements:**
- Accept a query string and optional filters (document, chapter, chunk_type)
- Return top_k (default 5) results
- Include metadata and similarity score in results
- Provide a `get_context_for_check(check_id)` convenience function

**Acceptance criteria:**
- `get_context_for_check("CHK-03")` returns chunks mentioning MRP / retail sale price
- Results include page numbers
- Results are ranked by relevance

---

## 22.3 Agent Task: OCR Pipeline (Person 5)

**File:** `backend/ocr/pipeline.py`  
**Purpose:** Orchestrate image preprocessing, OCR, and field extraction  
**Dependencies:** PIL/Pillow, google-cloud-vision (or pytesseract), requests  
**Input:** Image file path or bytes  
**Output:** Structured product facts in Section 7.2 schema  
**Interface that must not change:** Output schema (Section 7.2)  
**Implementation requirements:**
- Preprocess image: resize to max 2000px, enhance contrast, deskew if needed
- Send to OCR service (Google Cloud Vision API preferred)
- Get raw text + bounding boxes
- Use LLM (Gemini API) to structure raw text into fields
- Parse LLM response into the canonical schema
- Calculate overall_confidence from OCR confidence scores
- Detect languages in OCR output
- Find all MRP-like values (for CHK-10)
- Find quantity qualifiers (for CHK-07)

**Acceptance criteria:**
- Given a clear product image, returns a valid JSON matching Section 7.2 schema
- product_name, net_quantity, mrp fields are correctly extracted for well-labeled products
- Missing fields are null (not empty strings)
- Bounding boxes are present for detected fields

**Known edge cases:**
- Curved/cylindrical package text
- Multiple languages on same label
- Low contrast text
- Handwritten batch numbers

**What NOT to modify:** The output schema. If a field cannot be extracted, set its value to null.

---

## 22.4 Agent Task: Compliance Engine (Person 6)

**File:** `backend/compliance/engine.py`  
**Purpose:** Run all compliance checks against OCR facts  
**Dependencies:** None (pure Python logic)  
**Input:** Section 8.2 schema  
**Output:** Section 8.3 schema  
**Interface that must not change:** Input and output schemas  
**Implementation requirements:**
- Implement `run_all_checks(ocr_facts, product_context, legal_context)` function
- Call individual rule validators from `rules.py`
- Calculate overall status and compliance score
- Generate explanations using templates from RULE_MATRIX.md
- Include legal citations from RAG context

**File:** `backend/compliance/rules.py`  
**Purpose:** Individual rule validator functions  
**Implementation:** One function per CHK rule (see RULE_MATRIX.md for exact logic)  
**Each function signature:**
```python
def check_xxx(ocr_facts: dict, legal_context: dict) -> dict:
    """Returns a check result dict matching the checks[] item in Section 8.3"""
    pass
```

**Acceptance criteria:**
- All 10 golden test cases produce expected results
- No false positives on TEST-001 (compliant product)
- CHK-09 correctly skips when product is not imported

---

## 22.5 Agent Task: Backend API (Person 3)

**File:** `backend/api/inspections.py`  
**Purpose:** API endpoints for inspection workflow  
**Dependencies:** FastAPI, backend.ocr, backend.compliance, backend.database  
**Interface that must not change:** Endpoint paths and response formats (Section 12)  
**Implementation requirements:**
- POST /inspections: Accept file upload, save to disk, create DB record
- POST /inspections/{id}/analyze: Run full pipeline, save results to DB
- GET /inspections/{id}: Return full inspection with all checks
- GET /inspections: Return paginated list with filters
- POST /inspections/{id}/review: Save review action, update check status
- Handle errors gracefully (422 for bad input, 404 for not found, 500 for server errors)

**Acceptance criteria:**
- Can upload an image and get an inspection_id
- Can trigger analysis and get compliance results
- Can retrieve inspection details
- Can submit a review action

---

## 22.6 Agent Task: Frontend Results Page (Person 2)

**File:** `frontend/src/pages/InspectionResults.jsx`  
**Purpose:** The hero screen — display compliance results beautifully  
**Dependencies:** React, CSS (design tokens from Section 13.2)  
**Input:** Data from GET /inspections/{id}  
**Implementation requirements:**
- Large overall status badge (PASS=green, FAIL=red, REVIEW=yellow) with glassmorphism effect
- Circular compliance score gauge
- Summary bar showing passed/failed/review counts
- List of checks, each with: status icon, rule name, detected value, severity badge
- Expandable check cards showing: full reason, evidence, legal citation, recommendation
- Image viewer showing annotated image with bounding boxes
- "Generate Report" button
- "Review" buttons for REVIEW items
- Smooth animations on load and expand/collapse

**Acceptance criteria:**
- Page renders correctly for all three statuses (PASS, FAIL, REVIEW)
- All checks are displayed with correct status colors
- Expanding a check shows the legal citation
- Image viewer shows bounding boxes
- Page looks stunning and professional (dark theme, gradients, animations)

---

# 23. Final End-to-End Architecture

```
                    +------------------+
                    |   Product Image  |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Image Preprocess |
                    | (resize, enhance,|
                    |  deskew, denoise)|
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |   OCR Engine     |
                    | (Google Vision / |
                    |  Tesseract)      |
                    +--------+---------+
                             |
                    raw text + bounding boxes
                             |
                             v
                    +------------------+
                    | LLM-Assisted     |
                    | Field Extraction |
                    | (Gemini API)     |
                    +--------+---------+
                             |
                    Structured OCR Facts
                    (Section 7.2 schema)
                             |
              +--------------+--------------+
              |                             |
              v                             v
    +------------------+          +------------------+
    | Product Context  |          |    RAG System    |
    | (category hints, |          | (ChromaDB query) |
    |  import detect)  |          |                  |
    +--------+---------+          +--------+---------+
              |                             |
              |                  Retrieved Legal Clauses
              |                  (with citations)
              |                             |
              +-------------+---------------+
                            |
                            v
                   +------------------+
                   | Compliance Engine|
                   | (deterministic   |
                   |  rule validators)|
                   +--------+---------+
                            |
               Compliance Results
               (Section 8.3 schema)
                            |
              +-------------+---------------+
              |             |               |
              v             v               v
    +----------+   +----------+   +----------+
    | Evidence |   | Database |   |   API    |
    | Annotator|   | (SQLite) |   | (FastAPI)|
    +----------+   +----------+   +----+-----+
                                       |
                                       v
                              +------------------+
                              |    Frontend      |
                              |  (React + Vite)  |
                              +--------+---------+
                                       |
                        +--------------+--------------+
                        |              |              |
                        v              v              v
                  +---------+   +-----------+   +---------+
                  |Dashboard|   | Results   |   | Report  |
                  |         |   | (hero)    |   | Viewer  |
                  +---------+   +-----------+   +---------+
```

---

# 24. Acceptance Criteria

## Minimum for SIH Demo

1. [ ] User can log in
2. [ ] User can upload a product image
3. [ ] System extracts text via OCR and produces structured fields
4. [ ] System retrieves relevant legal provisions via RAG
5. [ ] System runs 8 compliance checks and returns PASS/FAIL/REVIEW
6. [ ] Each check includes: status, detected value, expected value, confidence, reason, evidence, legal citation
7. [ ] Overall status is correctly calculated
8. [ ] Compliance score is displayed
9. [ ] Results page shows all checks with expandable details
10. [ ] At least one violation detail shows bounding box evidence on the image
11. [ ] Legal citation links to specific rule and page number
12. [ ] Human review allows overriding a REVIEW result
13. [ ] Report can be generated (HTML format)
14. [ ] Dashboard shows basic analytics
15. [ ] System includes disclaimer about preliminary assessment
16. [ ] At least 3 golden test cases produce correct results
17. [ ] Demo runs without crashing for the 2-3 minute demo path

## Quality Bar

18. [ ] Frontend is visually impressive (dark theme, animations, glassmorphism)
19. [ ] No visible console errors during demo
20. [ ] Loading states are handled (no blank screens)
21. [ ] Error states are handled (meaningful error messages)
22. [ ] Response time: analysis completes within 30 seconds

---

# 25. Final Checklist Before SIH Demonstration

## T-24 Hours

- [ ] All 10 golden test cases verified
- [ ] Demo path rehearsed at least twice
- [ ] Mock OCR mode working as fallback
- [ ] All team members know the architecture and can explain it
- [ ] Backup laptop available

## T-2 Hours

- [ ] System running on demo machine
- [ ] Internet connection verified (for OCR API)
- [ ] Demo images loaded and accessible
- [ ] Login credentials working
- [ ] Dashboard has populated data

## During Demo

- [ ] Use the rehearsed demo path (TEST-006 as primary)
- [ ] Emphasize: RAG-based legal retrieval (not hardcoded rules)
- [ ] Emphasize: Deterministic compliance engine (not LLM decisions)
- [ ] Emphasize: Human-in-the-loop (not fully automated judgment)
- [ ] Emphasize: Traceable legal citations
- [ ] Use the phrase: "AI-assisted preliminary compliance assessment"
- [ ] If something fails: switch to backup demo case or explain the architecture

## Post-Demo Questions to Prepare For

1. "How does this differ from just using ChatGPT?" — Our system uses deterministic compliance rules with RAG-based legal retrieval, not LLM-only decisions
2. "Can this handle all product categories?" — MVP focuses on general retail packages; additional categories can be added by extending the rule matrix
3. "Is this legally valid?" — This is a preliminary assessment tool, not a legal certificate. It assists inspectors.
4. "How accurate is the OCR?" — We use Google Cloud Vision API with preprocessing. Confidence scores indicate reliability. Low confidence triggers human review.
5. "What about FSSAI regulations?" — Our current corpus covers the 2011 Rules. FSSAI and other sector-specific regulations are future scope — the RAG architecture is designed to incorporate additional documents.
6. "How would you scale this?" — Replace SQLite with PostgreSQL, deploy on cloud, add horizontal scaling for the API layer. The architecture is already designed for this.

---

# APPENDIX A: Security and Ethics

1. The system is described as an **AI-assisted preliminary compliance assessment** — never as a legally binding automated judgment
2. All evidence is **preserved** (original images, OCR output, compliance results)
3. **Confidence scores** are always displayed — never hidden
4. The system **distinguishes** OCR uncertainty from actual violations
5. **Human review** is always available — the system never claims infallibility
6. **Legal source references** are always provided — never "trust the AI"
7. **Disclaimers** appear on every result and every report
8. No personal data of consumers is collected or stored
9. Inspector identities are authenticated but basic JWT is sufficient for the prototype

---

# APPENDIX B: Python Dependencies (requirements.txt)

```
fastapi==0.115.0
uvicorn==0.30.0
python-multipart==0.0.9
pyjwt==2.8.0
passlib==1.7.4
python-dotenv==1.0.1
pymupdf==1.24.0
chromadb==0.5.0
sentence-transformers==3.0.0
google-cloud-vision==3.7.0
google-generativeai==0.7.0
Pillow==10.4.0
jinja2==3.1.4
pydantic==2.8.0
aiosqlite==0.20.0
pytest==8.3.0
httpx==0.27.0
```

---

*End of MASTER_BUILD_SPEC.md*

*This specification is the single source of truth. All coding agents must follow it. Do not deviate from the schemas, interfaces, or architecture defined herein without explicit approval.*
