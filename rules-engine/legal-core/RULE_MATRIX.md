# RULE_MATRIX — Regulatory Requirements Inventory & Compliance Rule Matrix

**Project:** SIH 2026 — PS 34: Packaged Commodities Compliance Checker  
**Source Documents:**  
- `rules2009.pdf` — The Legal Metrology Act, 2009 (Act No. 1 of 2010, 18 pages)  
- `rules2011.pdf` — The Legal Metrology (Packaged Commodities) Rules, 2011 (GSR 202(E), 43 pages)  

**Date:** 2026-09-05  
**Status:** AUTHORITATIVE — All subsequent coding agents must reference this document.

---

## 1. Document Relationship Analysis

### 1.1 What Each Document Represents

| Document | Nature | Content |
|---|---|---|
| `rules2009.pdf` | **Parent Act** — The Legal Metrology Act, 2009 | The enabling legislation. Establishes the framework for legal metrology in India. Defines powers, appointments, offences, penalties. Section 18 specifically empowers the Central Government to prescribe declarations on pre-packaged commodities. Section 52(2)(j) empowers rules for standard quantities and declarations. |
| `rules2011.pdf` | **Subordinate Rules** — The Legal Metrology (Packaged Commodities) Rules, 2011 | The operational rules made under Section 52(1) read with clauses (j) and (q) of Section 52(2) of the 2009 Act. These rules specify **exactly** what declarations must appear on packaged commodities, how they must appear, standard pack sizes, inspection procedures, and penalties for non-compliance. |

### 1.2 How They Relate

- The **2009 Act** is the parent statute. It grants rule-making power to the Central Government.
- The **2011 Rules** are the detailed operational regulations issued under that power.
- Section 18(1) of the Act says: *"No person shall manufacture, pack, sell... any pre-packaged commodity unless such package is in such standard quantities or number and bears thereon such declarations and particulars in such manner as may be prescribed."*
- The 2011 Rules are the "prescription" referenced by Section 18.
- Section 36 of the Act defines penalties for non-conforming packages — this is the enforcement backbone.
- The 2011 Rules **Chapter II (Rules 3–23)** contains the specific provisions for retail packages — this is where all label/declaration requirements live.
- The 2011 Rules also repeal the older Standards of Weights and Measures (Packaged Commodities) Rules, 1977 (Rule 34).

### 1.3 Which Provisions Are Relevant to Our Software System

**Directly relevant (label/declaration compliance):**
- 2011 Rules: Rules 3–18 (Chapter II — retail package declarations)
- 2011 Rules: Rule 5 + Second Schedule (standard pack sizes)
- 2011 Rules: Rule 6 (mandatory declarations)
- 2011 Rules: Rule 7 (display panel, font sizes)
- 2011 Rules: Rule 8 (where declarations must appear)
- 2011 Rules: Rule 9 (manner of declaration — language, legibility, contrast)
- 2011 Rules: Rule 10 (manufacturer/packer/importer name and address)
- 2011 Rules: Rules 11–13 (quantity declarations, units)
- 2011 Rules: Rule 18 (dealer obligations — no sale above MRP, no alteration)
- 2011 Rules: Rule 26 (exemptions)
- 2011 Rules: First Schedule (maximum permissible errors)

**Contextual (penalties, enforcement authority):**
- 2009 Act: Section 18 (declaration requirements — enabling provision)
- 2009 Act: Section 36 (penalties for non-standard packages)
- 2011 Rules: Rule 32 (penalties for rule violations)

**Not directly relevant to label-image scanning:**
- 2009 Act: Chapters on weights/measures standards, verification/stamping, officer appointments
- 2011 Rules: Rules 19–23 (physical inspection procedures, sampling, quantity testing)
- 2011 Rules: Rules 24 (wholesale packages — different scope)
- 2011 Rules: Rules 27–31 (registration of manufacturers)
- 2011 Rules: Schedules 3–7 (physical testing procedures)

### 1.4 Supersession / Amendment Notes

Several provisions in the 2011 Rules have footnotes indicating amendments via GSR 748(E) dated 24.10.2011, with changes effective from 01.07.2012. These include:
- Rule 5 proviso (non-standard size declaration) — *withdrawn* w.e.f. 01.07.2012
- Rule 6(1)(d) third proviso (rubber stamp for month/year) — *withdrawn* w.e.f. 01.07.2012
- Rule 12(6) (exaggerated quantity words) — *amended* w.e.f. 01.07.2012
- Rule 26(a) proviso (10g–20g packages) — *withdrawn* w.e.f. 01.07.2012
- Fourth Schedule, item 15 (ice cream volume to weight) — *amended* w.e.f. 01.07.2012

**For our system:** Since these amendments took effect in 2012 (over 14 years ago), we should apply the post-amendment state. However, the exact final text is not always fully clear from the PDF. Where ambiguous, we flag it below and default to the stricter interpretation.

---

## 2. Full Regulatory Requirements Inventory

Each requirement below is traced to its source.

---

### Category A: Clearly Image-Detectable Requirements

| Req ID | Doc | Rule | Sub-rule | Page | Requirement | Applicability | Pkg Comm? | Image? | OCR? | CV? | Deterministic? | Human? | Severity | Priority | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | 2011 | 6(1)(a) | — | 5 | **Name and address of manufacturer** (or manufacturer+packer, or importer for imports) must be declared | All retail packages | Yes | Yes | Yes | No | Yes (presence check) | Partial | CRITICAL | **MVP** | Can check presence of text resembling a name/address. Cannot verify correctness of the address. |
| REQ-002 | 2011 | 6(1)(b) | — | 5 | **Common or generic name of commodity** must be declared | All retail packages | Yes | Yes | Yes | No | Yes (presence check) | Partial | CRITICAL | **MVP** | Can detect if a product name exists. Cannot verify if it is the correct generic name. |
| REQ-003 | 2011 | 6(1)(c) | — | 5 | **Net quantity** in standard units of weight/measure/number must be declared | All retail packages | Yes | Yes | Yes | No | Yes (presence + format) | Partial | CRITICAL | **MVP** | Can detect quantity text. Can validate unit format. Cannot verify actual net content. |
| REQ-004 | 2011 | 6(1)(d) | — | 5-6 | **Month and year of manufacture/pre-packing/import** must be declared | All retail packages (with exceptions per proviso A) | Yes | Yes | Yes | No | Yes (presence + format) | Partial | HIGH | **MVP** | Exceptions: bidis, certain LPG cylinders. Can validate date format. |
| REQ-005 | 2011 | 6(1)(e) | — | 6 | **Retail sale price (MRP)** must be declared | All retail packages (with exceptions per proviso C) | Yes | Yes | Yes | No | Yes (presence + format) | Partial | CRITICAL | **MVP** | Format: "MRP Rs ____ incl. of all taxes" or equivalent. Exceptions: bidis, price-controlled LPG. |
| REQ-006 | 2011 | 6(2) | — | 7 | **Consumer care information** — name, address, telephone, email (if available) of person/office for complaints | All retail packages | Yes | Yes | Yes | No | Yes (presence check) | Partial | HIGH | **MVP** | Can detect phone number patterns, email patterns. |
| REQ-007 | 2011 | 9(4) | — | 10 | **Language** — declarations must be in **Hindi (Devanagari) or English** | All retail packages | Yes | Yes | Yes | No | Partial | Yes | MEDIUM | **OPTIONAL** | OCR can detect script type but reliability is limited. Better as REVIEW. |
| REQ-008 | 2011 | 2(m) | — | 3 | **MRP format** — "Maximum or Max. retail price Rs/... inclusive of all taxes" or "MRP Rs/... incl. of all taxes" | All packages with MRP | Yes | Yes | Yes | No | Yes (regex) | No | HIGH | **MVP** | Can validate MRP text format against prescribed patterns. |
| REQ-009 | 2011 | 13(5) | — | 14 | **Units must be in International System (SI units)** — no non-SI systems | All retail packages | Yes | Yes | Yes | No | Yes (unit check) | No | MEDIUM | **MVP** | Can check that quantity uses g/kg/ml/L/m/cm, not oz/lb/fl.oz etc. |
| REQ-010 | 2011 | 10(1) | — | 11 | **Complete address** of manufacturer/packer/importer — postal address including street, number, city+state or PIN code | All retail packages | Yes | Yes | Yes | No | Partial | Yes | HIGH | **OPTIONAL** | Can detect if an address-like text block is present. Cannot verify completeness reliably. |

### Category B: Partially Image-Detectable Requirements

| Req ID | Doc | Rule | Sub-rule | Page | Requirement | Applicability | Pkg Comm? | Image? | OCR? | CV? | Deterministic? | Human? | Severity | Priority | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| REQ-011 | 2011 | 9(1)(a) | — | 10 | Declarations must be **legible and prominent** | All retail packages | Yes | Partial | No | Yes | No | Yes | MEDIUM | **OPTIONAL** | Requires subjective assessment. Could flag based on OCR confidence as proxy. |
| REQ-012 | 2011 | 9(1)(b) | — | 10 | Numerals of MRP and net quantity must be printed in **colour contrasting conspicuously with background** | All retail packages | Yes | Partial | No | Yes | Partial | Yes | MEDIUM | **FUTURE** | Requires color analysis of image regions. Complex CV. |
| REQ-013 | 2011 | 7(2)-(3) | — | 8-9 | **Minimum font size** — numerals for net quantity must meet height requirements per Table-I/Table-II (1mm-6mm depending on quantity) | All retail packages | Yes | Partial | No | Yes | Partial | Yes | MEDIUM | **FUTURE** | Requires estimating real-world dimensions from image. Very unreliable without reference object. |
| REQ-014 | 2011 | 6(3) | — | 7 | **No individual stickers** for altering required declarations (except for reducing MRP) | All retail packages | Yes | Partial | No | Yes | No | Yes | HIGH | **FUTURE** | Detecting stickers requires advanced CV. |
| REQ-015 | 2011 | 5 | + Second Schedule | 4, 29-32 | Commodity must be packed in **standard quantities** as specified in Second Schedule | Specific commodities listed in Second Schedule | Yes | Partial | Yes | No | Yes (lookup) | Partial | HIGH | **OPTIONAL** | If product category is known AND net quantity is extracted, can cross-check against Second Schedule. But category identification from image is uncertain. |
| REQ-016 | 2011 | 12(6) | post-amendment | 13 | Quantity declaration shall not contain **misleading words** like "minimum", "not less than", "average", "about", "approximately" | All retail packages | Yes | Yes | Yes | No | Yes (keyword search) | No | MEDIUM | **MVP** | Can search OCR text for prohibited qualifiers near quantity declarations. |
| REQ-017 | 2011 | 6(1)(f) | — | 6 | Where sizes are relevant, **dimensions** of the commodity must be declared | Conditional — only where size is relevant | Yes | Partial | Yes | No | Partial | Yes | LOW | **FUTURE** | Applicability is conditional on product type. |
| REQ-018 | 2011 | 18(5) | — | 16 | No one shall **obliterate, smudge or alter the MRP** | All retail packages | Yes | Partial | No | Yes | No | Yes | HIGH | **FUTURE** | Detecting physical alteration requires advanced CV. |
| REQ-019 | 2011 | 10(1) 2nd proviso | — | 11 | For commodities **manufactured outside India and packed in India**, must show packer/importer name+address on principal display panel | Imported goods packed in India | Yes | Partial | Yes | No | Partial | Yes | MEDIUM | **OPTIONAL** | Requires knowing if product is imported. Could detect "Imported by" or "Country of Origin" text. |
| REQ-020 | 2011 | 9(3) | — | 10 | If package has outer container/wrapper, it must also contain all declarations (unless transparent and inner declarations visible) | Packages with outer wrappers | Yes | Partial | Yes | No | No | Yes | LOW | **FUTURE** | Cannot reliably determine inner vs outer packaging from a single image. |

### Category C: Requirements Not Reliably Detectable from Image

| Req ID | Doc | Rule | Sub-rule | Page | Requirement | Why Not Image-Detectable |
|---|---|---|---|---|---|---|
| REQ-021 | 2011 | 3(a) | — | 4 | Chapter II does not apply to packages over 25kg/25L (except cement/fertilizer up to 50kg) | Requires knowing actual quantity — may be partially inferred from net quantity text but threshold determination is ambiguous |
| REQ-022 | 2011 | 3(b) | — | 4 | Chapter II does not apply to packages for industrial/institutional consumers | Cannot determine buyer type from image |
| REQ-023 | 2011 | 11(1)-(4) | — | 11-12 | Net quantity must exclude wrapper weight and correspond to actual received quantity | Requires physical measurement |
| REQ-024 | 2011 | 18(2) | — | 16 | No sale at price exceeding MRP | Requires knowing actual sale price, not visible on package |
| REQ-025 | 2011 | 19-22 | — | 17-22 | Physical inspection procedures, sampling, quantity testing | Requires physical measurement |
| REQ-026 | 2011 | 23 | — | 22 | Deceptive package detection | Requires physical assessment of package dimensions vs content |
| REQ-027 | 2011 | 27 | — | 24 | Registration of manufacturer/packer/importer | Requires database lookup, not image-based |
| REQ-028 | 2011 | 26(a) | — | 24 | Exemption: packages 10g/10ml or less are exempt from all rules | Requires knowing actual quantity — could be inferred from net quantity text |
| REQ-029 | 2009 | 18(1) | — | 8 | Package must be in standard quantities and bear prescribed declarations | Meta-requirement — implemented through the 2011 Rules |
| REQ-030 | 2009 | 36 | — | 11 | Penalty for non-conforming packages | Penalty provision — not a checkable requirement but needed for citation |

---

## 3. Detectability Summary

| Category | Count | Description |
|---|---|---|
| **A — Clearly Image-Detectable** | 10 | Presence/format checks via OCR text analysis |
| **B — Partially Image-Detectable** | 10 | Require conditional logic, CV analysis, or contextual knowledge |
| **C — Not Image-Detectable** | 10 | Require physical measurement, external databases, or buyer context |

---

## 4. Final MVP Compliance Rule Matrix

These are the **10 rules selected for the five-day prototype**, chosen based on:
1. Direct traceability to the 2011 Rules
2. Feasibility of OCR-based detection
3. Deterministic validation capability
4. High impact for SIH demonstration

---

### RULE CHK-01: Product/Commodity Name Present

| Field | Value |
|---|---|
| **rule_id** | `CHK-01` |
| **human_name** | Product Name Declaration |
| **legal_source** | Rule 6(1)(b), Legal Metrology (Packaged Commodities) Rules, 2011 |
| **source_page** | Page 5 of rules2011.pdf |
| **req_id** | REQ-002 |
| **applicable_category** | All retail packages |
| **required_or_conditional** | REQUIRED |
| **input_field** | `product_name` |
| **detection_method** | OCR text extraction, search for prominent text block identifiable as product/commodity name |
| **normalization_method** | Trim whitespace, normalize casing |
| **validation_logic** | Check that `product_name` is not null/empty and contains at least one alphabetic word |
| **PASS_condition** | `product_name` is non-null, non-empty, OCR confidence >= 0.7 |
| **FAIL_condition** | `product_name` is null after OCR extraction with overall image OCR confidence >= 0.8 |
| **REVIEW_condition** | `product_name` is null but overall image OCR confidence < 0.8; OR `product_name` confidence < 0.7 |
| **severity** | CRITICAL |
| **evidence_needed** | Extracted text value, bounding box coordinates, OCR confidence score |
| **explanation_template** | "Rule 6(1)(b) of the Legal Metrology (Packaged Commodities) Rules, 2011 requires every package to declare the common or generic name of the commodity. {result_detail}" |

---

### RULE CHK-02: Net Quantity Declaration Present and Valid

| Field | Value |
|---|---|
| **rule_id** | `CHK-02` |
| **human_name** | Net Quantity Declaration |
| **legal_source** | Rule 6(1)(c), Rule 13, Legal Metrology (Packaged Commodities) Rules, 2011 |
| **source_page** | Page 5, 13-14 of rules2011.pdf |
| **req_id** | REQ-003, REQ-009 |
| **applicable_category** | All retail packages |
| **required_or_conditional** | REQUIRED |
| **input_field** | `net_quantity` (object: `{value, unit, raw_text}`) |
| **detection_method** | OCR + regex matching for patterns like `\d+\s*(g|kg|ml|L|litre|liter|cm|m|mm|N|U)\b` |
| **normalization_method** | Parse numeric value and unit. Normalize unit to SI standard (g to g, gm to g, ml to ml, ltr to L, etc.) |
| **validation_logic** | 1) Presence check: net_quantity must not be null. 2) Unit check: unit must be SI (per Rule 13(5)). 3) No prohibited qualifiers (per REQ-016): raw text near quantity must not contain "minimum", "not less than", "average", "about", "approximately". |
| **PASS_condition** | net_quantity present with valid SI unit, no prohibited qualifiers, confidence >= 0.7 |
| **FAIL_condition** | net_quantity is null with image confidence >= 0.8; OR unit is non-SI (oz, lb, fl.oz, etc.); OR prohibited qualifier detected |
| **REVIEW_condition** | net_quantity null with image confidence < 0.8; OR unit unclear; OR quantity confidence < 0.7 |
| **severity** | CRITICAL |
| **evidence_needed** | Extracted raw text, parsed value+unit, bounding box, confidence, any prohibited qualifiers found |
| **explanation_template** | "Rules 6(1)(c) and 13 of the Legal Metrology (Packaged Commodities) Rules, 2011 require net quantity declaration in standard SI units. {result_detail}" |

---

### RULE CHK-03: MRP Declaration Present and Correctly Formatted

| Field | Value |
|---|---|
| **rule_id** | `CHK-03` |
| **human_name** | MRP Declaration |
| **legal_source** | Rule 6(1)(e), Rule 2(m), Legal Metrology (Packaged Commodities) Rules, 2011 |
| **source_page** | Page 3, 6 of rules2011.pdf |
| **req_id** | REQ-005, REQ-008 |
| **applicable_category** | All retail packages (except bidis, price-controlled LPG per provisos) |
| **required_or_conditional** | REQUIRED (with exceptions) |
| **input_field** | `mrp` (object: `{value, raw_text, includes_tax_declaration}`) |
| **detection_method** | OCR + regex for patterns: `(MRP\|M\.R\.P\|Max\.?\s*Retail\s*Price\|Maximum\s*Retail\s*Price)\s*:?\s*Rs\.?\s*[\d,.]+` |
| **normalization_method** | Extract numeric price value. Check for "inclusive of all taxes" / "incl. of all taxes" text nearby. |
| **validation_logic** | 1) Presence check. 2) Format check: must include "inclusive of all taxes" or equivalent per Rule 2(m). 3) Price must be a positive number. |
| **PASS_condition** | MRP found, format matches prescribed pattern, "inclusive of all taxes" phrase present, confidence >= 0.7 |
| **FAIL_condition** | MRP not found with image confidence >= 0.8; OR MRP found but missing "inclusive of all taxes" declaration |
| **REVIEW_condition** | MRP not found with image confidence < 0.8; OR MRP confidence < 0.7; OR tax inclusion text unclear |
| **severity** | CRITICAL |
| **evidence_needed** | Raw MRP text, parsed value, tax inclusion phrase, bounding box, confidence |
| **explanation_template** | "Rules 6(1)(e) and 2(m) of the Legal Metrology (Packaged Commodities) Rules, 2011 require declaration of MRP in the format 'MRP Rs ___ inclusive of all taxes'. {result_detail}" |

---

### RULE CHK-04: Manufacturer / Packer / Importer Name and Address

| Field | Value |
|---|---|
| **rule_id** | `CHK-04` |
| **human_name** | Manufacturer/Packer/Importer Information |
| **legal_source** | Rule 6(1)(a), Rule 10, Legal Metrology (Packaged Commodities) Rules, 2011 |
| **source_page** | Page 5, 10-11 of rules2011.pdf |
| **req_id** | REQ-001, REQ-010 |
| **applicable_category** | All retail packages |
| **required_or_conditional** | REQUIRED |
| **input_field** | `manufacturer` (object: `{name, address, raw_text}`), `packer`, `importer` |
| **detection_method** | OCR + keyword search for: "Manufactured by", "Mfd. by", "Packed by", "Packer", "Imported by", "Marketed by", or presence of company name with address-like text (city, state, PIN code pattern `\d{6}`) |
| **normalization_method** | Extract entity name and address block. Check for PIN code / city / state. |
| **validation_logic** | 1) At least one entity (manufacturer OR packer OR importer) must be present with name. 2) Address should contain identifiable location info (PIN code or city name). |
| **PASS_condition** | At least one entity with name+address detected, confidence >= 0.7 |
| **FAIL_condition** | No manufacturer/packer/importer text found with image confidence >= 0.8 |
| **REVIEW_condition** | Entity found but address incomplete; OR low confidence; OR multiple entities with unclear roles |
| **severity** | CRITICAL |
| **evidence_needed** | Detected entity names, address text, role keywords, bounding boxes, confidence |
| **explanation_template** | "Rules 6(1)(a) and 10 of the Legal Metrology (Packaged Commodities) Rules, 2011 require the name and complete address of the manufacturer (or packer/importer where applicable). {result_detail}" |

---

### RULE CHK-05: Date of Manufacture / Packing / Import

| Field | Value |
|---|---|
| **rule_id** | `CHK-05` |
| **human_name** | Manufacturing/Packing Date Declaration |
| **legal_source** | Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011 |
| **source_page** | Page 5-6 of rules2011.pdf |
| **req_id** | REQ-004 |
| **applicable_category** | All retail packages (except bidis, incense sticks, certain LPG — per proviso A) |
| **required_or_conditional** | REQUIRED (with specific exceptions) |
| **input_field** | `manufacturing_date` (object: `{month, year, raw_text}`) |
| **detection_method** | OCR + regex for date patterns: `(Mfg\.?\s*Date\|Mfd\.?\s*Date\|MFD\|Manufactured\|Packed\|Pkd)[\s:]*(\d{1,2}[/\-\.]\d{2,4}\|\w+[\s,]*\d{4}\|\d{2}[/\-]\d{4})` and also `(Best\s*Before\|Use\s*By\|Exp\.?\s*Date\|Expiry)` |
| **normalization_method** | Parse into month and year. Per Rule 6(1)(d) and Explanation I, "month and year" may be expressed in words or numerals. |
| **validation_logic** | 1) Presence check: at least month and year must be present. 2) Date should be parseable. 3) Date should not be in the future (sanity check). |
| **PASS_condition** | Manufacturing/packing date with at least month+year detected, confidence >= 0.7 |
| **FAIL_condition** | No date found with image confidence >= 0.8 |
| **REVIEW_condition** | Date found but unparseable; OR confidence < 0.7; OR product may be in exempt category (bidis, etc.) |
| **severity** | HIGH |
| **evidence_needed** | Raw date text, parsed month/year, bounding box, confidence |
| **explanation_template** | "Rule 6(1)(d) of the Legal Metrology (Packaged Commodities) Rules, 2011 requires declaration of the month and year of manufacture, pre-packing, or import. {result_detail}" |

---

### RULE CHK-06: Consumer Care / Complaint Contact Information

| Field | Value |
|---|---|
| **rule_id** | `CHK-06` |
| **human_name** | Consumer Care Information |
| **legal_source** | Rule 6(2), Legal Metrology (Packaged Commodities) Rules, 2011 |
| **source_page** | Page 7 of rules2011.pdf |
| **req_id** | REQ-006 |
| **applicable_category** | All retail packages |
| **required_or_conditional** | REQUIRED |
| **input_field** | `consumer_care` (object: `{phone, email, address, raw_text}`) |
| **detection_method** | OCR + pattern matching: phone patterns `[\d\s\-]{10,}`, email patterns `\S+@\S+\.\S+`, keywords: "Consumer", "Customer", "Care", "Helpline", "Toll free", "Complaints" |
| **normalization_method** | Extract phone number, email address, and/or contact address. |
| **validation_logic** | 1) At least one contact channel (phone number, email, or address with "complaints"/"consumer care" context) must be present. |
| **PASS_condition** | At least one contact method (phone/email) with consumer-care context detected, confidence >= 0.7 |
| **FAIL_condition** | No consumer care information found with image confidence >= 0.8 |
| **REVIEW_condition** | Phone/email found but without consumer-care context keywords; OR confidence < 0.7 |
| **severity** | HIGH |
| **evidence_needed** | Detected phone number, email, keywords, bounding boxes, confidence |
| **explanation_template** | "Rule 6(2) of the Legal Metrology (Packaged Commodities) Rules, 2011 requires every package to bear the name, address, telephone number, and email address (if available) of the person or office that can be contacted for consumer complaints. {result_detail}" |

---

### RULE CHK-07: Quantity Declaration — No Misleading Qualifiers

| Field | Value |
|---|---|
| **rule_id** | `CHK-07` |
| **human_name** | No Misleading Quantity Qualifiers |
| **legal_source** | Rule 12(6) (post-2012 amendment), Legal Metrology (Packaged Commodities) Rules, 2011 |
| **source_page** | Page 13 of rules2011.pdf |
| **req_id** | REQ-016 |
| **applicable_category** | All retail packages |
| **required_or_conditional** | REQUIRED |
| **input_field** | Full OCR text around net quantity declaration |
| **detection_method** | OCR text search in vicinity of net quantity for prohibited words |
| **normalization_method** | Lowercase, remove extra whitespace |
| **validation_logic** | Search for: "minimum", "not less than", "average", "about", "approximately" or similar qualifiers within text context of quantity declaration |
| **PASS_condition** | No prohibited qualifiers found near quantity declaration |
| **FAIL_condition** | Prohibited qualifier detected with high confidence |
| **REVIEW_condition** | OCR confidence low in the quantity region; OR partial match of prohibited words |
| **severity** | MEDIUM |
| **evidence_needed** | Prohibited word(s) found, surrounding text context, bounding box |
| **explanation_template** | "Rule 12(6) of the Legal Metrology (Packaged Commodities) Rules, 2011 (as amended) prohibits the use of words or expressions in the quantity declaration that tend to create an exaggerated, misleading, or inadequate impression, including terms like 'minimum', 'not less than', 'average', 'about', or 'approximately'. {result_detail}" |

---

### RULE CHK-08: Declaration Language (Hindi/English)

| Field | Value |
|---|---|
| **rule_id** | `CHK-08` |
| **human_name** | Declaration Language Compliance |
| **legal_source** | Rule 9(4), Legal Metrology (Packaged Commodities) Rules, 2011 |
| **source_page** | Page 10 of rules2011.pdf |
| **req_id** | REQ-007 |
| **applicable_category** | All retail packages |
| **required_or_conditional** | REQUIRED |
| **input_field** | OCR-detected language / script |
| **detection_method** | OCR language detection — check if declarations are in Devanagari script or English (Latin script) |
| **normalization_method** | Identify script family of major declaration text blocks |
| **validation_logic** | At least one of the declaration blocks should be in English or Hindi/Devanagari. Other languages are permitted in addition to Hindi/English but not as sole language. |
| **PASS_condition** | English or Devanagari text detected in declarations |
| **FAIL_condition** | — (should not auto-fail; this is inherently subjective from an image) |
| **REVIEW_condition** | Declarations appear to be only in a script other than Devanagari or Latin; OR OCR cannot determine script |
| **severity** | MEDIUM |
| **evidence_needed** | Detected script types, sample text in each script |
| **explanation_template** | "Rule 9(4) of the Legal Metrology (Packaged Commodities) Rules, 2011 requires that declarations be in Hindi (Devanagari script) or English. Additional languages are permitted alongside Hindi or English. {result_detail}" |
| **implementation_priority** | OPTIONAL |

---

### RULE CHK-09: Country of Origin for Imported Goods

| Field | Value |
|---|---|
| **rule_id** | `CHK-09` |
| **human_name** | Country of Origin / Importer Declaration |
| **legal_source** | Rule 6(1)(a) (imported packages), Rule 10(1) second proviso, Legal Metrology (Packaged Commodities) Rules, 2011 |
| **source_page** | Page 5, 11 of rules2011.pdf |
| **req_id** | REQ-019 |
| **applicable_category** | Imported packages only |
| **required_or_conditional** | CONDITIONAL — only if product is imported |
| **input_field** | `country_of_origin`, `importer` |
| **detection_method** | OCR search for: "Country of Origin", "Made in", "Product of", "Imported by", "Importer" |
| **normalization_method** | Extract country name. Determine if product is imported based on presence of import-related keywords. |
| **validation_logic** | IF import indicators detected (e.g., "Imported by"), THEN country of origin AND importer name+address should be present. |
| **PASS_condition** | Either: (a) no import indicators so N/A, or (b) import indicators present AND country of origin AND importer details present |
| **FAIL_condition** | Import indicators present but country of origin OR importer details missing, with confidence >= 0.8 |
| **REVIEW_condition** | Ambiguous whether product is imported; OR confidence < 0.7 |
| **severity** | HIGH |
| **evidence_needed** | Import indicator text, country of origin text, importer details, bounding boxes |
| **explanation_template** | "Rule 6(1)(a) of the Legal Metrology (Packaged Commodities) Rules, 2011 requires that imported packages declare the name and address of the importer. Where a commodity manufactured outside India is packed in India, Rule 10(1) requires the packer/importer name and address on the principal display panel. {result_detail}" |

---

### RULE CHK-10: MRP Sticker Compliance

| Field | Value |
|---|---|
| **rule_id** | `CHK-10` |
| **human_name** | MRP Sticker / Alteration Check |
| **legal_source** | Rule 6(3), Rule 18(5)-(6), Legal Metrology (Packaged Commodities) Rules, 2011 |
| **source_page** | Page 7, 16 of rules2011.pdf |
| **req_id** | REQ-014, REQ-018 |
| **applicable_category** | All retail packages |
| **required_or_conditional** | REQUIRED |
| **input_field** | `mrp` (plus any secondary MRP detected), visual analysis of MRP region |
| **detection_method** | OCR: detect multiple MRP values on same package. CV: detect visual discontinuities / sticker-like regions over MRP area |
| **normalization_method** | Compare all detected MRP values. |
| **validation_logic** | 1) If multiple MRP values detected, flag. 2) Per Rule 6(3), sticker for reduced MRP is allowed but must NOT cover original MRP. 3) No increasing of MRP via sticker. |
| **PASS_condition** | Single MRP detected; OR two MRPs detected where sticker MRP is less than or equal to original MRP |
| **FAIL_condition** | — (should not auto-fail from image alone; alteration detection is unreliable) |
| **REVIEW_condition** | Multiple MRP values detected; OR visual anomaly in MRP region; OR original MRP appears covered/obscured |
| **severity** | HIGH |
| **evidence_needed** | All detected MRP values, positions, visual assessment notes |
| **explanation_template** | "Rule 6(3) prohibits individual stickers for altering required declarations. A sticker with a reduced MRP is permitted but must not cover the original MRP. Rule 18(5) prohibits obliterating, smudging, or altering the MRP. {result_detail}" |
| **implementation_priority** | OPTIONAL |

---

## 5. Rule Priority Summary

### MVP Rules (Must implement for demo — 8 rules)

| ID | Name | Severity | Validation Type |
|---|---|---|---|
| CHK-01 | Product Name | CRITICAL | Presence check |
| CHK-02 | Net Quantity | CRITICAL | Presence + format + unit + qualifier check |
| CHK-03 | MRP | CRITICAL | Presence + format check |
| CHK-04 | Manufacturer/Packer/Importer | CRITICAL | Presence check |
| CHK-05 | Manufacturing Date | HIGH | Presence + format check |
| CHK-06 | Consumer Care Info | HIGH | Presence + pattern check |
| CHK-07 | No Misleading Qualifiers | MEDIUM | Keyword search |
| CHK-09 | Country of Origin (imports) | HIGH | Conditional presence check |

### Optional Rules (If time permits — 2 rules)

| ID | Name | Severity | Validation Type |
|---|---|---|---|
| CHK-08 | Language Compliance | MEDIUM | Script detection |
| CHK-10 | MRP Sticker/Alteration | HIGH | Multi-value detection |

### Future Scope Rules (Post-hackathon)

| ID | Name | Why Deferred |
|---|---|---|
| REQ-011 | Legibility assessment | Subjective, requires advanced CV |
| REQ-012 | Color contrast | Requires color analysis |
| REQ-013 | Font size compliance | Requires real-world dimension estimation |
| REQ-015 | Standard pack size (Second Schedule) | Requires product category identification |
| REQ-017 | Dimension declarations | Conditional applicability |
| REQ-018 | MRP physical alteration | Requires advanced CV |
| REQ-020 | Inner/outer packaging | Cannot assess from single image |

---

## 6. Ambiguities and Flags

**AMB-01:** Rule 6(1)(a) Explanation III states that for packages containing food articles, PFA Act 1954 provisions apply instead of Rule 6(1)(a) for manufacturer/packer declarations. The PFA Act 1954 has since been superseded by the Food Safety and Standards Act, 2006 (FSSAI). Our system does not have FSSAI regulations in its corpus. **Decision for MVP:** Apply Rule 6(1)(a) uniformly, but note in the report that food articles may have additional requirements under FSSAI.

**AMB-02:** Rule 6(1)(d) provisos exempt certain categories (food articles under PFA/FSSAI, seeds under Seeds Act, cosmetics under Drugs and Cosmetics Rules). Our system cannot reliably determine product category from an image. **Decision for MVP:** Check for date presence universally, but issue REVIEW (not FAIL) when date is absent and product category is uncertain.

**AMB-03:** The proviso to Rule 6(1)(e) regarding alcoholic beverages (State Excise Laws apply) creates a category-dependent rule. **Decision for MVP:** Check MRP universally; note in explanations that State Excise Laws may apply for alcoholic beverages.

**AMB-04 (CRITICAL):** Absence in OCR does not equal absence on package. A field not detected by OCR could be because: (a) the field is genuinely missing from the package, (b) OCR failed to detect it due to image quality, angle, obscured text, or font issues, (c) the field is on another face of the package not visible in the image. Our system must always distinguish between these possibilities using confidence scores and explicitly state this limitation.

**AMB-05:** "Best Before / Use By" is mentioned in the problem statement but the 2011 Rules only explicitly require "month and year of manufacture/pre-packing/import" (Rule 6(1)(d)). Best Before / Use By dates are governed by FSSAI regulations for food products. Our system should still extract these dates if detected, but the compliance check per the 2011 Rules is for manufacturing date, not expiry date.

---

## 7. Penalty Reference (For Citation)

| Violation Type | Penalty Source | Penalty |
|---|---|---|
| Non-conforming pre-packaged commodity (wrong/missing declarations) | Section 36(1), Legal Metrology Act, 2009 | First offence: fine up to Rs 25,000. Second: up to Rs 50,000. Subsequent: Rs 50,000 to Rs 1,00,000 or imprisonment up to 1 year or both. |
| Error in net quantity | Section 36(2), Legal Metrology Act, 2009 | Fine Rs 10,000 to Rs 50,000. Subsequent: up to Rs 1,00,000 or imprisonment up to 1 year or both. |
| Contravention of Rules 27-31 (registration) | Rule 32(1), 2011 Rules | Fine of Rs 4,000 |
| Other rule contraventions | Rule 32(2), 2011 Rules | Fine of Rs 2,000 |

---

*End of RULE_MATRIX.md*
