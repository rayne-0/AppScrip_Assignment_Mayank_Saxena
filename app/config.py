"""
Application configuration loaded from environment variables.
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from .env file or environment variables."""

    # --- Gemini AI ---
    GEMINI_API_KEY: str = ""

    # --- JWT Authentication ---
    JWT_SECRET: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60

    # --- Rate Limiting ---
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # --- App ---
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
