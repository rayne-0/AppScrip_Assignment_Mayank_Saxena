"""
Trade Opportunities API — Main FastAPI Application

A FastAPI service that analyzes market data and provides trade
opportunity insights for specific sectors in India.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import HealthResponse
from app.routes.auth_routes import router as auth_router
from app.routes.analyze import router as analyze_router

# ─── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("  Trade Opportunities API — Starting up")
    logger.info(f"  Environment: {settings.APP_ENV}")
    logger.info(f"  Gemini API Key: {'configured' if settings.GEMINI_API_KEY else 'NOT SET'}")
    logger.info(f"  Rate Limit: {settings.RATE_LIMIT_REQUESTS} req / {settings.RATE_LIMIT_WINDOW_SECONDS}s")
    logger.info("=" * 60)

    if not settings.GEMINI_API_KEY:
        logger.warning(
            "⚠️  GEMINI_API_KEY is not set! The /analyze endpoint will fail. "
            "Get a free key at https://aistudio.google.com/apikey"
        )

    yield

    logger.info("Trade Opportunities API — Shutting down")


# ─── App Initialization ────────────────────────────────────────────────────────

app = FastAPI(
    title="Trade Opportunities API",
    description=(
        "A FastAPI service that analyzes market data and provides trade opportunity "
        "insights for specific sectors in India. Powered by Google Gemini AI and "
        "real-time web search data.\n\n"
        "## Getting Started\n"
        "1. Get a guest token: `POST /auth/token`\n"
        "2. Use the token: `GET /analyze/{sector}` with `Authorization: Bearer <token>`\n\n"
        "## Example Sectors\n"
        "`pharmaceuticals`, `technology`, `agriculture`, `textiles`, `automobile`, "
        "`renewable energy`, `steel`, `chemicals`"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every incoming request with method, path, and response time."""
    import time
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)"
    )
    return response


# ─── Global Exception Handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a clean JSON response."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


# ─── Routes ────────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(analyze_router)


# ─── Health Check ──────────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
    description="Returns the current health status of the API.",
)
async def health_check():
    """Simple health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc),
    )


@app.get(
    "/",
    tags=["System"],
    summary="API Root",
    description="Welcome message with quick-start instructions.",
)
async def root():
    """Root endpoint with API info."""
    return {
        "message": "Welcome to the Trade Opportunities API",
        "version": "1.0.0",
        "docs": "/docs",
        "quick_start": {
            "step_1": "POST /auth/token → Get a guest JWT token",
            "step_2": "GET /analyze/{sector} → Analyze a sector (use Bearer token)",
            "example_sectors": [
                "pharmaceuticals",
                "technology",
                "agriculture",
                "textiles",
                "automobile",
                "renewable energy",
            ],
        },
    }
