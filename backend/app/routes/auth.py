"""
APIRouter: Authentication

Endpoints
---------
POST /api/v1/auth/login  - Validate credentials and return a token
GET  /api/v1/auth/me     - Get the currently authenticated user
POST /api/v1/auth/logout - Invalidate the current session token
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, UserRead
from app.services.auth import authenticate, create_token, get_user_by_id, revoke_token, resolve_token

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

DBSession = Annotated[Session, Depends(get_db)]

security = HTTPBearer()

def get_current_user(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Dependency to get the current authenticated user from the Bearer token."""
    token = credentials.credentials
    user_id = resolve_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login to get a session token",
    description="Validates username and password and returns a Bearer token. Prototype authentication.",
)
def login(
    payload: LoginRequest,
    db: DBSession,
) -> dict:
    user = authenticate(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    token = create_token(user.id)
    return {
        "success": True,
        "message": "Login successful",
        "user": user,
        "token": token,
    }


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Returns the currently authenticated user details.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout and invalidate token",
    description="Revokes the current session token.",
)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    revoked = revoke_token(token)
    if not revoked:
        # For idempotency, we can just return success anyway or a specific message.
        return {"success": True, "message": "Token was already invalid or expired"}
    return {"success": True, "message": "Logged out successfully"}
