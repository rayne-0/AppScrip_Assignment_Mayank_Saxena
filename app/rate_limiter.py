"""
In-memory sliding window rate limiter.

Tracks request timestamps per user and enforces a configurable
requests-per-window limit.
"""

import time
import logging
from collections import defaultdict

from fastapi import Depends, HTTPException, status, Request

from app.config import settings
from app.auth import get_current_user

logger = logging.getLogger(__name__)

# ─── In-Memory Store ────────────────────────────────────────────────────────────

# { "username": [timestamp1, timestamp2, ...] }
_request_log: dict[str, list[float]] = defaultdict(list)


# ─── Helpers ────────────────────────────────────────────────────────────────────

def _cleanup_old_entries(username: str, window: float) -> None:
    """Remove timestamps older than the sliding window."""
    cutoff = time.time() - window
    _request_log[username] = [
        ts for ts in _request_log[username] if ts > cutoff
    ]


def check_rate_limit_for_user(username: str) -> None:
    """
    Check if a user has exceeded the rate limit.
    Raises HTTPException 429 if the limit is exceeded.
    """
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    max_requests = settings.RATE_LIMIT_REQUESTS

    _cleanup_old_entries(username, window)

    if len(_request_log[username]) >= max_requests:
        oldest = _request_log[username][0]
        retry_after = int(oldest + window - time.time()) + 1
        logger.warning(f"Rate limit exceeded for user: {username}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    # Record this request
    _request_log[username].append(time.time())


# ─── FastAPI Dependency ─────────────────────────────────────────────────────────

async def rate_limit(username: str = Depends(get_current_user)) -> str:
    """
    FastAPI dependency that enforces rate limiting.
    Must be used after get_current_user in the dependency chain.
    Returns the username for downstream use.
    """
    check_rate_limit_for_user(username)
    return username


def cleanup_all_stale_entries() -> int:
    """
    Periodic cleanup: remove all users with no recent requests.
    Returns the number of entries cleaned up.
    """
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    cutoff = time.time() - window
    cleaned = 0

    stale_users = [
        user for user, timestamps in _request_log.items()
        if all(ts <= cutoff for ts in timestamps)
    ]
    for user in stale_users:
        del _request_log[user]
        cleaned += 1

    if cleaned:
        logger.debug(f"Cleaned up {cleaned} stale rate-limit entries")
    return cleaned
