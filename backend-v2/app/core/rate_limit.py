"""Simple in-memory rate limiter for login attempts."""

import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

_login_attempts: dict[str, list[float]] = defaultdict(list)

MAX_ATTEMPTS = 10
WINDOW_SECONDS = 300  # 5 minutes


def is_rate_limited(identifier: str) -> bool:
    """Return True if *identifier* has exceeded the rate limit."""
    now = time.monotonic()
    cutoff = now - WINDOW_SECONDS
    _login_attempts[identifier] = [t for t in _login_attempts[identifier] if t > cutoff]
    if len(_login_attempts[identifier]) >= MAX_ATTEMPTS:
        logger.warning(
            "Rate limited: %s (%d attempts in %ds)",
            identifier,
            len(_login_attempts[identifier]),
            WINDOW_SECONDS,
        )
        return True
    return False


def record_attempt(identifier: str) -> None:
    """Record a login attempt for *identifier*."""
    _login_attempts[identifier].append(time.monotonic())
