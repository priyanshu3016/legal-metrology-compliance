"""
Authentication service — app/services/auth.py

Provides:
  - PBKDF2-HMAC-SHA256 password hashing (stdlib only, no extra deps)
  - Password verification
  - User lookup / login
  - In-memory session token store  (prototype — replace with JWT in production)
  - Demo user auto-creation on first startup

PROTOTYPE NOTE
--------------
Tokens are stored in process memory.  They are lost on server restart.
For production, replace with signed JWT (python-jose) or a token table in SQLite.

Demo credentials:
  username : inspector
  password : inspector123
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User

# ---------------------------------------------------------------------------
# In-memory session store   { token: user_id }
# ---------------------------------------------------------------------------
_SESSIONS: dict[str, int] = {}

DEMO_USERNAME = "inspector"
DEMO_PASSWORD = "inspector123"
DEMO_NAME     = "Demo Inspector"
DEMO_ROLE     = "inspector"

# ---------------------------------------------------------------------------
# Password hashing — PBKDF2-HMAC-SHA256
# Format: "pbkdf2:sha256:<iterations>$<hex-salt>$<hex-hash>"
# ---------------------------------------------------------------------------
_ITERATIONS = 260_000  # NIST-recommended minimum for PBKDF2-SHA256 as of 2024


def hash_password(plain: str) -> str:
    """Return a salted PBKDF2-SHA256 hash string for storage."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, _ITERATIONS)
    return f"pbkdf2:sha256:{_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(plain: str, stored_hash: str | None) -> bool:
    """Verify *plain* against a stored hash produced by :func:`hash_password`."""
    if not stored_hash:
        return False
    try:
        _, _, rest = stored_hash.split(":", 2)
        iterations_str, salt_hex, dk_hex = rest.split("$")
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(dk_hex)
        candidate = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, iterations)
        return hmac.compare_digest(candidate, expected)
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Session tokens
# ---------------------------------------------------------------------------

def create_token(user_id: int) -> str:
    """Generate a cryptographically random Bearer token and store it."""
    token = secrets.token_hex(32)   # 256-bit token
    _SESSIONS[token] = user_id
    return token


def resolve_token(token: str) -> Optional[int]:
    """Return the user_id for a valid token, or None."""
    return _SESSIONS.get(token)


def revoke_token(token: str) -> bool:
    """Remove a token from the session store.  Returns True if it existed."""
    return _SESSIONS.pop(token, None) is not None


# ---------------------------------------------------------------------------
# User operations
# ---------------------------------------------------------------------------

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def authenticate(db: Session, username: str, password: str) -> User | None:
    """Verify credentials and return the User on success, else None."""
    user = get_user_by_username(db, username)
    if user is None:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# ---------------------------------------------------------------------------
# Demo user bootstrap
# ---------------------------------------------------------------------------

def ensure_demo_user(db: Session) -> None:
    """Create the demo inspector account if the users table is empty.

    This is called once at application startup.  If any user already exists,
    this function is a no-op.

    Demo credentials:
      username : inspector
      password : inspector123
    """
    count = db.query(User).count()
    if count > 0:
        return  # preserve existing users

    demo = User(
        username=DEMO_USERNAME,
        password_hash=hash_password(DEMO_PASSWORD),
        name=DEMO_NAME,
        role=DEMO_ROLE,
        badge_number="DEMO-001",
        is_active=True,
    )
    db.add(demo)
    db.commit()
