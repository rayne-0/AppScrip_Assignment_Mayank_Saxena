"""
Pydantic models for request/response schemas.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ─── Auth Models ────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiry in seconds")
    username: str


# ─── Analysis Models ────────────────────────────────────────────────────────────

class AnalysisSource(BaseModel):
    """A single source used in the analysis."""
    title: str
    url: str
    snippet: str = ""


class SectorAnalysisResponse(BaseModel):
    """Schema for the sector analysis response."""
    sector: str = Field(description="The sector that was analyzed")
    report: str = Field(description="Structured markdown analysis report")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    sources: list[AnalysisSource] = Field(default_factory=list)
    cached: bool = Field(default=False, description="Whether this result was served from cache")


# ─── Error Models ───────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    status_code: int


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = "healthy"
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
