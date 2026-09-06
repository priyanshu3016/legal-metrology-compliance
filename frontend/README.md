# 🛡️ PackCheck AI — Legal Metrology Compliance Enforcement Platform
> **Smart India Hackathon (SIH 2026)**  
> Automated Package Inspection, OCR Text Extraction & Legal Metrology (Packaged Commodities) Rules Verification System

---

## 📌 Executive Summary
**PackCheck AI** is an enterprise-grade, AI-assisted compliance screening and evidence management platform designed for **Legal Metrology Enforcement Officers** under the **Ministry of Consumer Affairs, Food & Public Distribution (Government of India)**.

The platform transforms manual, error-prone field packaging inspections into an automated computer-vision inspection pipeline:
1. **Multi-panel package image capture & OCR extraction**
2. **Deterministic rule validation** against the *Legal Metrology (Packaged Commodities) Rules, 2011* (including recent amendments for Unit Sale Price, country of origin, and dual declarations)
3. **Automated violation detection & severity classification**
4. **Court-admissible inspection report generation** with cryptographic timestamping and officer signature blocks

---

## 🚀 Quick Start Guide

### Prerequisites
- Node.js (v18 or higher recommended)
- npm (v9 or higher)

### 1. Installation
```bash
cd packcheck-ai
npm install
```

### 2. Run Local Development Server
```bash
npm run dev
```
The application will launch at: **`http://localhost:5173`** (or `http://127.0.0.1:5173`)

### 3. Production Build
```bash
npm run build
npm run preview
```

---

## 🔐 Demonstration Credentials
The application is pre-configured with active session defaults and pre-filled login fields for zero-friction evaluation:

| Field | Demo Credential | Description |
|---|---|---|
| **Username** | `officer.rajesh` | Senior Legal Metrology Officer |
| **Password** | `packcheck2026` | *(Any non-empty password accepted)* |
| **Officer** | Rajesh Kumar | Senior Enforcement Officer |
| **Badge Number** | `LMO-DL-2847` | Delhi NCR Enforcement Division |

---

## 🗺️ Application Architecture & Routes

| Route | Page | Purpose & Key Features |
|---|---|---|
| `/login` | **Officer Login** | Government portal authentication, branding, feature showcase, pre-filled demo notice |
| `/dashboard` | **Analytics Dashboard** | Live compliance trend (Recharts), status donut chart, violation categories, recent inspections table, activity feed |
| `/inspection/new` | **New Inspection** | Multi-panel package image drag-and-drop, location/jurisdiction selector, reference tags, AI trigger |
| `/inspection/processing` | **AI Pipeline Status** | 6-stage animated computer-vision pipeline (Image validation → OCR → Rule Matching → Report generation) |
| `/inspection/result` | **Compliance Showcase** | Circular compliance gauge, 4-tab breakdown (Extracted Fields, Rule Checks, OCR Confidence, Evidence preview) |
| `/inspection/violations` | **Violation Analysis** | Violation cards with severity badges, rule references, recommended statutory actions, officer remarks editor |
| `/inspection/evidence` | **Evidence Manager** | Multi-image viewer with bounding box overlay overlays, raw OCR monospace terminal stream, hardware metadata |
| `/inspection/report` | **Official Report** | Print-optimized legal inspection report with Ministry headers, check table, violation notice, officer signature block |
| `/history` | **Audit History** | Searchable, filterable, sortable historical registry with multi-column sorting and pagination |
| `/history/:id` | **Inspection Detail** | Read-only audit view with tabbed inspection records and inspection metadata |
| `/rules` | **Rule Reference** | Interactive Legal Metrology Rules database with filterable categories, exemptions, and statutory references |
| `/settings` | **System Settings** | Officer profile editor, notification preference toggles, display settings, and system diagnostics |

---

## 🔌 AI & Backend Integration Architecture

The frontend is architected with a decoupled service layer located in `src/services/api.js`.

### Ready Integration Endpoints
```javascript
// OCR & Computer Vision Pipeline
POST /api/v1/inspections/ocr-analyze
Payload: FormData { images: File[], location: string, referenceNumber: string }
Response: { boundingBoxes, ocrConfidence, extractedFields }

// Legal Metrology Rule Engine
POST /api/v1/inspections/validate-rules
Payload: { extractedData: object, commodityCategory: string }
Response: { score: number, checks: [], violations: [] }

// Report Dispatch & PDF Export
POST /api/v1/inspections/:id/generate-pdf
Response: { pdfUrl: string, hash: string }
```

---

## 📋 Technology Stack
- **Framework:** React 19 + Vite 8
- **Styling:** Tailwind CSS v4 (`@tailwindcss/vite`)
- **Routing:** React Router v7
- **Data Visualization:** Recharts
- **Icons:** Lucide React
- **HTTP Client:** Axios with request/response interceptors
- **State Management:** React Context API (`AuthContext`, `InspectionContext`, `ToastContext`)
