"""
Legal Metrology Compliance Backend - FastAPI Application Entry Point.

Provides:
  GET /                                        -> service banner
  GET /api/v1/health                           -> health check
  POST   /api/v1/inspections                   -> create inspection
  GET    /api/v1/inspections                   -> list inspections
  GET    /api/v1/inspections/{id}              -> inspection detail
  PATCH  /api/v1/inspections/{id}              -> update inspection
  DELETE /api/v1/inspections/{id}              -> delete inspection
  POST   /api/v1/inspections/{id}/images       -> upload label images
  GET    /api/v1/inspections/{id}/images       -> list images
  DELETE /api/v1/inspections/{id}/images/{img} -> delete image
  POST   /api/v1/inspections/{id}/extracted-data -> submit AI/OCR results
  GET    /api/v1/inspections/{id}/extracted-data -> get extracted results
  POST   /api/v1/inspections/{id}/compliance     -> run compliance engine
  GET    /api/v1/inspections/{id}/compliance     -> get compliance result
  POST   /api/v1/inspections/{id}/evidence       -> create evidence
  GET    /api/v1/inspections/{id}/evidence       -> list evidence
  DELETE /api/v1/evidence/{evidence_id}          -> delete evidence
  POST   /api/v1/inspections/{id}/report         -> generate PDF report
  GET    /api/v1/inspections/{id}/reports        -> list reports
  GET    /api/v1/reports/{report_id}/download    -> download PDF report
  POST   /api/v1/auth/login                      -> login to get token
  GET    /api/v1/auth/me                         -> get current user
  POST   /api/v1/auth/logout                     -> logout
  Swagger UI at /docs
  ReDoc at /redoc

Start with:
  venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import SessionLocal, init_db
from app.routes.auth import router as auth_router
from app.routes.compliance import router as compliance_router
from app.routes.dashboard import router as dashboard_router
from app.routes.evidence import evidence_router, inspection_router as evidence_inspection_router
from app.routes.extraction import router as extraction_router
from app.routes.images import UPLOADS_DIR
from app.routes.images import router as images_router
from app.routes.inspections import router as inspections_router
from app.routes.reports import inspection_router as reports_inspection_router
from app.routes.reports import report_router
from app.routes.inspect import router as inspect_router
from app.services.auth import ensure_demo_user
from app.services.report import REPORTS_DIR

# ---------------------------------------------------------------------------
# Lifespan – runs on startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Startup:  initialise the database (create tables if they don't exist).
    Shutdown: nothing additional is required for SQLite; connection pools are
              cleaned up automatically by SQLAlchemy.
    """
    # ---- startup ----
    init_db()
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)  # ensure uploads/ exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)  # ensure reports/ exists

    with SessionLocal() as db:
        ensure_demo_user(db)

    yield  # application runs here

    # ---- shutdown ----
    # Future: close Redis connections, stop background workers, etc.


# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Legal Metrology Compliance Backend",
    description=(
        "REST API for the Legal Metrology Compliance system. "
        "Handles product label inspection, compliance rule evaluation, "
        "and report generation."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(inspections_router)
app.include_router(images_router)
app.include_router(extraction_router)
app.include_router(compliance_router)
app.include_router(evidence_inspection_router)
app.include_router(evidence_router)
app.include_router(reports_inspection_router)
app.include_router(report_router)
app.include_router(inspect_router)

# ---------------------------------------------------------------------------
# Built-in utility routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Root"])
async def root() -> dict:
    """Service banner – confirms the backend is reachable."""
    return {"message": "Legal Metrology Compliance Backend is running"}


@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint – used by load-balancers and monitoring tools."""
    return {"status": "ok", "service": "Legal Metrology Compliance Backend"}
