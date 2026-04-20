"""
JWT-based authentication with guest mode support.

Provides:
- User registration (in-memory)
- Login with username/password
- Guest token generation (no signup required)
- JWT token verification dependency
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger(__name__)

# ─── Password Hashing ──────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── In-Memory User Store ──────────────────────────────────────────────────────

users_db: dict[str, dict] = {}
# Format: { "username": { "password_hash": "...", "is_guest": False, "created_at": datetime } }

# ─── Security Scheme ───────────────────────────────────────────────────────────

security = HTTPBearer(auto_error=False)


# ─── Token Helpers ──────────────────────────────────────────────────────────────

def create_access_token(username: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token for the given username."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    )
    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the username, or None if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


# ─── User Operations ───────────────────────────────────────────────────────────

def register_user(username: str, password: str) -> dict:
    """Register a new user. Raises ValueError if username exists."""
    if username in users_db:
        raise ValueError("Username already exists")

    users_db[username] = {
        "password_hash": pwd_context.hash(password),
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
    }
    logger.info(f"Registered new user: {username}")
    return {"username": username, "is_guest": False}


def authenticate_user(username: str, password: str) -> Optional[str]:
    """Authenticate user with username/password. Returns username if valid."""
    user = users_db.get(username)
    if not user or user.get("is_guest"):
        return None
    if not pwd_context.verify(password, user["password_hash"]):
        return None
    return username


def create_guest_user() -> str:
    """Create a guest user with auto-generated username."""
    guest_id = f"guest_{uuid.uuid4().hex[:8]}"
    users_db[guest_id] = {
        "password_hash": None,
        "is_guest": True,
        "created_at": datetime.now(timezone.utc),
    }
    logger.info(f"Created guest user: {guest_id}")
    return guest_id


# ─── FastAPI Dependencies ───────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    FastAPI dependency to extract the current user from the JWT token.
    Returns the username string.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Get a token via POST /auth/token or POST /auth/register",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = verify_token(credentials.credentials)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return username
