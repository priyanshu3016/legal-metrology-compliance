# Legal Metrology Compliance – Backend

FastAPI-based REST API backend for the Legal Metrology Compliance system.

---

## Technology Stack

| Layer | Library | Version |
|---|---|---|
| Framework | FastAPI | 0.115.0 |
| ASGI server | Uvicorn | 0.30.6 |
| ORM | SQLAlchemy | 2.0.35 |
| Data validation | Pydantic | 2.9.2 |
| Settings | pydantic-settings | 2.5.2 |
| File uploads | python-multipart | 0.0.12 |
| Environment | python-dotenv | 1.0.1 |
| HTTP client | httpx | 0.27.2 |

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py        # Package marker
│   ├── main.py            # FastAPI app, CORS, startup, root routes
│   ├── database.py        # SQLAlchemy engine, session, Base, init_db
│   ├── models/            # ORM models (added in later steps)
│   ├── schemas/           # Pydantic request/response schemas
│   ├── routes/            # APIRouter modules
│   └── services/          # Business-logic services
├── uploads/               # Uploaded label images (git-ignored)
├── reports/               # Generated compliance reports (git-ignored)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python 3.12 (the `venv/` directory must already exist inside `backend/`)
- The virtual environment is expected at `backend\venv\`

### 2. Install Dependencies

Run from inside the `backend\` directory:

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and adjust values as needed:

```powershell
copy .env.example .env
```

Default values work out of the box for local development (SQLite).

---

## Running the Server

```powershell
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

The server will start at **http://127.0.0.1:8000**

---

## Verification

After starting, verify the following endpoints:

### Root banner

```
GET http://127.0.0.1:8000/
```

Expected response:
```json
{"message": "Legal Metrology Compliance Backend is running"}
```

### Health check

```
GET http://127.0.0.1:8000/api/v1/health
```

Expected response:
```json
{"status": "ok", "service": "Legal Metrology Compliance Backend"}
```

### Interactive API docs

Open in your browser:

- Swagger UI → http://127.0.0.1:8000/docs
- ReDoc       → http://127.0.0.1:8000/redoc

---

## Database

By default the application uses **SQLite** and creates `packcheck.db` in the
`backend/` directory on first startup.  The file is git-ignored.

To use a different database, set `DATABASE_URL` in your `.env` file, for
example:

```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/packcheck
```

---

## CORS

The API allows cross-origin requests from:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

These origins match the default Vite dev-server port used by the frontend.

---

## API Reference

### Inspection Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/inspections` | Create a new inspection |
| GET | `/api/v1/inspections` | List inspections (`?skip=0&limit=20&status=pending`) |
| GET | `/api/v1/inspections/{id}` | Inspection detail with images / declarations / violations |
| PATCH | `/api/v1/inspections/{id}` | Update status, compliance_score, location, product_id |
| DELETE | `/api/v1/inspections/{id}` | Delete inspection and all related records (CASCADE) |

**Create inspection:**
```bash
curl -X POST http://localhost:8000/api/v1/inspections \
  -H "Content-Type: application/json" \
  -d '{"reference_number": "LM-2026-0001", "location": "Delhi"}'
```

---

### Image Upload Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/inspections/{id}/images` | Upload one or more label images (JPG/PNG/WebP, max 10 MB each) |
| GET | `/api/v1/inspections/{id}/images` | List all images for an inspection |
| DELETE | `/api/v1/inspections/{id}/images/{image_id}` | Delete image record + physical file |

**Upload a single image:**
```bash
curl -X POST http://localhost:8000/api/v1/inspections/1/images \
  -F "files=@/path/to/label.jpg" \
  -F "panel_type=front"
```

**Upload multiple images at once:**
```bash
curl -X POST http://localhost:8000/api/v1/inspections/1/images \
  -F "files=@front.jpg" \
  -F "files=@back.png" \
  -F "panel_type=label"
```

**List images:**
```bash
curl http://localhost:8000/api/v1/inspections/1/images
```

**Delete an image:**
```bash
curl -X DELETE http://localhost:8000/api/v1/inspections/1/images/3
```

**Image upload rules:**
- Accepted formats: `.jpg`, `.jpeg`, `.png`, `.webp`
- Maximum size: **10 MB per file**
- Files stored in `backend/uploads/` with UUID-based names (e.g. `inspection_1_<uuid>.jpg`)
- Only metadata is stored in SQLite — binary data is never written to the database

---

## Running Tests

```powershell
# Database integration test (Steps 3 + 4)
venv\Scripts\python.exe test_db.py

# Image upload integration test (Step 5)
venv\Scripts\python.exe test_step5.py

# AI/OCR data integration test (Step 6)
venv\Scripts\python.exe test_step6.py
```

---

## AI/OCR Integration Contract (Step 6)

### Architecture

```
AI/OCR Pipeline  ->  POST /extracted-data  ->  Declaration rows in SQLite
                                                       |
                                              Rules Engine (Step 7)
                                              evaluates compliance
```

**Key principle:** The backend stores extracted facts. It does **not** decide
whether a product is legally compliant — that is the rules engine's job.

### Extracted Data Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/inspections/{id}/extracted-data` | Submit AI/OCR extracted label fields |
| GET  | `/api/v1/inspections/{id}/extracted-data` | Get all extracted fields for an inspection |

### Submit extracted data

```bash
curl -X POST http://localhost:8000/api/v1/inspections/1/extracted-data \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Tata Salt",
    "manufacturer": "Tata Consumer Products Ltd.",
    "net_quantity": "1 kg",
    "mrp": "Rs.30",
    "date_of_packing": "08/2026",
    "best_before": "6 months",
    "consumer_care": "1800-123-4567",
    "country_of_origin": "India",
    "confidence": {
      "product_name": 0.98,
      "net_quantity": 0.99,
      "mrp": 0.97
    }
  }'
```

### Upsert behavior

- **Existing field** -> value and confidence are updated in-place.
- **New field** -> a new Declaration row is inserted.
- **Unmentioned fields** -> left unchanged (no deletion of historical data).

### Inspection status transitions (extraction)

| Trigger | Status set to |
|---------|--------------|
| POST extracted-data received | `processing` |
| POST extracted-data committed successfully | `completed` |

### Per-field confidence

- Range: **0.0** (no confidence) to **1.0** (certain).
- Values outside this range are rejected with HTTP 422.
- Confidence is optional per field — omit a field from the map if unknown.

---

## Implemented Steps

| Step | Status | Description |
|------|--------|-------------|
| 1 | Done | FastAPI foundation, CORS, health endpoint |
| 2 | Done | SQLAlchemy ORM models (9 tables), SQLite |
| 3 | Done | Inspection CRUD API + Pydantic schemas |
| 4 | Done | Inspection API connected and tested against SQLite |
| 5 | Done | Label image upload, listing, and deletion |
| 6 | Done | AI/OCR extracted-data submission and retrieval |
| 7 | Done | Deterministic Compliance Rules Engine |
| 8 | Done | Evidence and Report Generation APIs |
| 9 | Done | Inspector/User Authentication API |

---

## Authentication API (Step 9)

**PROTOTYPE NOTICE:** The current authentication uses in-memory session Bearer tokens. They are lost on server restart. This is intended for the SIH prototype phase.

### Demo Credentials

A demo inspector account is automatically created on first startup if no users exist:
- **Username:** `inspector`
- **Password:** `inspector123`

### Authentication Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Validate credentials and receive a token |
| GET  | `/api/v1/auth/me`    | Get the current authenticated user |
| POST | `/api/v1/auth/logout`| Invalidate the current session token |

### Example: Login Request

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "inspector", "password": "inspector123"}'
```

### Example: Authenticated Request with Authorization Header

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <your_token_here>"
```
