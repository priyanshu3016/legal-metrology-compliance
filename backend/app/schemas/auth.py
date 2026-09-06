"""
Pydantic v2 schemas for authentication.

Used by:
  POST /api/v1/auth/login
  GET  /api/v1/auth/me
  POST /api/v1/auth/logout
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Credentials for login."""
    username: str = Field(..., min_length=1, description="Inspector username")
    password: str = Field(..., min_length=1, description="Inspector password")


class UserRead(BaseModel):
    """Public representation of a user (no password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    role: str
    badge_number: str | None = None
    is_active: bool
    created_at: datetime


class LoginResponse(BaseModel):
    """Returned on successful login."""

    success: bool = True
    message: str
    user: UserRead
    token: str = Field(description="Bearer token — include as 'Authorization: Bearer <token>'")


class LogoutResponse(BaseModel):
    """Returned on logout."""

    success: bool = True
    message: str
