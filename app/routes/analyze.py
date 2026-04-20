"""
Sector analysis route — the main endpoint of the API.

GET /analyze/{sector} → Structured markdown trade opportunity report
"""

import re
import time
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.rate_limiter import rate_limit
from app.models import SectorAnalysisResponse, AnalysisSource
from app.services.search import search_market_data
from app.services.analyzer import analyze_sector

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analysis"])

# ─── In-Memory Cache ────────────────────────────────────────────────────────────

# { "sector": { "response": SectorAnalysisResponse, "timestamp": float } }
_analysis_cache: dict[str, dict] = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes

# ─── Session Tracking ──────────────────────────────────────────────────────────

# List of { "user": str, "sector": str, "timestamp": datetime }
_request_history: list[dict] = []


# ─── Helpers ────────────────────────────────────────────────────────────────────

def _validate_sector(sector: str) -> str:
    """Validate and normalize the sector name."""
    sector = sector.strip().lower()

    if not sector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sector name cannot be empty",
        )

    if len(sector) < 2 or len(sector) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sector name must be between 2 and 50 characters",
        )

    # Allow letters, spaces, hyphens, and ampersands (e.g. "oil & gas")
    if not re.match(r"^[a-zA-Z\s\-&]+$", sector):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sector name must contain only letters, spaces, hyphens, and ampersands",
        )

    return sector


def _get_cached(sector: str) -> SectorAnalysisResponse | None:
    """Return cached analysis if still valid, else None."""
    cached = _analysis_cache.get(sector)
    if cached and (time.time() - cached["timestamp"]) < CACHE_TTL_SECONDS:
        logger.info(f"Cache hit for sector: {sector}")
        response = cached["response"]
        response.cached = True
        return response
    return None


def _set_cache(sector: str, response: SectorAnalysisResponse) -> None:
    """Store analysis result in cache."""
    _analysis_cache[sector] = {
        "response": response,
        "timestamp": time.time(),
    }


# ─── Main Endpoint ─────────────────────────────────────────────────────────────

@router.get(
    "/analyze/{sector}",
    response_model=SectorAnalysisResponse,
    summary="Analyze trade opportunities for a sector",
    description=(
        "Accepts a sector name (e.g., 'pharmaceuticals', 'technology', 'agriculture') "
        "and returns a structured markdown market analysis report with current trade "
        "opportunities in India. Results are cached for 30 minutes."
    ),
    responses={
        200: {"description": "Successful analysis report"},
        400: {"description": "Invalid sector name"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Analysis failed"},
    },
)
async def analyze_trade_opportunities(
    sector: str,
    username: str = Depends(rate_limit),
):
    """
    Main analysis endpoint.

    Pipeline:
    1. Validate & normalize sector name
    2. Check cache for recent analysis
    3. Search web for current market data
    4. Send data to Gemini AI for analysis
    5. Return structured markdown report
    """
    sector = _validate_sector(sector)

    # Track the request
    _request_history.append({
        "user": username,
        "sector": sector,
        "timestamp": datetime.now(timezone.utc),
    })

    # Check cache first
    cached_response = _get_cached(sector)
    if cached_response:
        return cached_response

    # Step 1: Search for market data
    try:
        search_results, search_context = search_market_data(sector)
    except Exception as e:
        logger.error(f"Search failed for sector '{sector}': {e}")
        search_results, search_context = [], ""

    # Step 2: AI Analysis
    try:
        report = await analyze_sector(sector, search_context)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during analysis. Please try again.",
        )

    # Build response
    sources = [
        AnalysisSource(title=r.title, url=r.url, snippet=r.snippet)
        for r in search_results
    ]

    response = SectorAnalysisResponse(
        sector=sector,
        report=report,
        generated_at=datetime.now(timezone.utc),
        sources=sources,
        cached=False,
    )

    # Cache the result
    _set_cache(sector, response)

    logger.info(f"Analysis complete for sector '{sector}' by user '{username}'")
    return response
