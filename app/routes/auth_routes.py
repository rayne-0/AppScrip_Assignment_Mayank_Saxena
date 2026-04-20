"""
Authentication routes — register, login, and guest token generation.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.auth import (
    register_user,
    authenticate_user,
    create_guest_user,
    create_access_token,
)
from app.config import settings
from app.models import UserCreate, TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new account with username and password. Returns a JWT token.",
)
async def register(user: UserCreate):
    """Register a new user and return a JWT token."""
    try:
        register_user(user.username, user.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    token = create_access_token(user.username)
    logger.info(f"User registered and token issued: {user.username}")

    return TokenResponse(
        access_token=token,
        username=user.username,
        expires_in=settings.JWT_EXPIRY_MINUTES * 60,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with username and password",
    description="Authenticate with credentials and receive a JWT token.",
)
async def login(user: UserCreate):
    """Login and return a JWT token."""
    username = authenticate_user(user.username, user.password)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(username)
    logger.info(f"User logged in: {username}")

    return TokenResponse(
        access_token=token,
        username=username,
        expires_in=settings.JWT_EXPIRY_MINUTES * 60,
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Get a guest token",
    description="Generate a guest JWT token instantly — no registration required.",
)
async def guest_token():
    """Create a guest user and return a JWT token. No signup needed."""
    guest_username = create_guest_user()
    token = create_access_token(guest_username)
    logger.info(f"Guest token issued: {guest_username}")

    return TokenResponse(
        access_token=token,
        username=guest_username,
        expires_in=settings.JWT_EXPIRY_MINUTES * 60,
    )
