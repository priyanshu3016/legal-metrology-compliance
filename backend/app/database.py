"""
Database configuration for Legal Metrology Compliance Backend.

Uses SQLAlchemy 2.x with SQLite by default.
DATABASE_URL can be overridden via the environment variable DATABASE_URL.
"""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///./packcheck.db",
)

# ---------------------------------------------------------------------------
# SQLAlchemy engine
# ---------------------------------------------------------------------------
# check_same_thread=False is required for SQLite when used with FastAPI because
# the same connection may be accessed from different threads during dependency
# injection.
connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,          # Set to True for SQL query logging during development
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Declarative base – all ORM models will inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------
def _migrate_evidence_columns() -> None:
    """Add columns to the evidence table that were introduced after initial creation.

    SQLite supports ALTER TABLE ... ADD COLUMN but not IF NOT EXISTS.
    We query PRAGMA table_info to check which columns already exist.
    """
    with engine.connect() as conn:
        existing = {
            row[1]
            for row in conn.execute(
                __import__("sqlalchemy").text("PRAGMA table_info(evidence)")
            )
        }
        if "field_name" not in existing:
            conn.execute(__import__("sqlalchemy").text(
                "ALTER TABLE evidence ADD COLUMN field_name VARCHAR(150)"
            ))
            conn.commit()
        if "violation_id" not in existing:
            conn.execute(__import__("sqlalchemy").text(
                "ALTER TABLE evidence ADD COLUMN violation_id INTEGER REFERENCES violations(id)"
            ))
            conn.commit()


def _migrate_user_columns() -> None:
    """Add password_hash and is_active columns to the users table if absent.

    These columns were added in Step 9 to support authentication.
    Existing user rows (if any) get password_hash=NULL and is_active=1.
    """
    with engine.connect() as conn:
        existing = {
            row[1]
            for row in conn.execute(
                __import__("sqlalchemy").text("PRAGMA table_info(users)")
            )
        }
        if "password_hash" not in existing:
            conn.execute(__import__("sqlalchemy").text(
                "ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)"
            ))
            conn.commit()
        if "is_active" not in existing:
            conn.execute(__import__("sqlalchemy").text(
                "ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"
            ))
            conn.commit()


def init_db() -> None:
    """Create all tables defined by ORM models (if they don't already exist).

    This is called once during application startup via the FastAPI lifespan
    context manager in app/main.py.

    All ORM model classes must be imported before Base.metadata.create_all()
    is called, otherwise SQLAlchemy has no knowledge of those tables.
    The import of app.models triggers each model module, which registers the
    table metadata on Base.
    """
    import app.models  # noqa: F401 – side-effect: registers all ORM models

    Base.metadata.create_all(bind=engine)
    _migrate_evidence_columns()  # add new columns to existing evidence table
    _migrate_user_columns()      # add auth columns to existing users table



# ---------------------------------------------------------------------------
# FastAPI dependency – yields a database session per request
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and guarantee it is closed after the request.

    Usage in a route::

        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
