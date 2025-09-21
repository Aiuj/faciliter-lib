"""faciliter_lib.llm.rate_limiter

Utilities for client-side rate limiting of API requests.

This module provides a small asyncio-friendly RateLimiter that enforces both
a requests-per-minute rolling window and a requests-per-second sustained rate.
It is intended for use by LLM provider clients to avoid hitting remote API
rate limits from a single process.

Example:
    from faciliter_lib.llm.rate_limiter import RateLimitConfig, RateLimiter
    config = RateLimitConfig(requests_per_minute=120, requests_per_second=2.0)
    limiter = RateLimiter(config)
    # In async code:
    await limiter.acquire()
"""

import asyncio
import time
from typing import List
from dataclasses import dataclass
from faciliter_lib import get_module_logger


logger = get_module_logger()

@dataclass
class RateLimitConfig:
    """Configuration for the RateLimiter.

    Attributes:
        requests_per_minute: Maximum number of requests allowed in any rolling
            60-second window. When this limit is reached, acquire() will sleep
            until the oldest recorded request falls outside the 60s window.
        requests_per_second: Maximum sustained requests per second. This is
            enforced as a minimum interval between consecutive requests.
        burst_allowance: Reserved for brief bursts above the sustained rate.
            The current implementation keeps the parameter for compatibility
            and future use; callers should treat it as advisory.
    """
    requests_per_minute: int = 60
    requests_per_second: float = 1.0
    burst_allowance: int = 5

class RateLimiter:
    """Simple asyncio-compatible rate limiter for API requests.

    The limiter records timestamps of recent requests (a sliding window) and
    serializes access with an asyncio.Lock so multiple coroutines may safely
    call acquire() concurrently. The limiter enforces:
      - A rolling requests-per-minute limit (count of timestamps within last 60s).
      - A requests-per-second limit expressed as a minimum interval between requests.

    Notes:
      - acquire() may sleep the caller to satisfy rate limits; it does not raise.
      - The class is intentionally lightweight and kept in-process; it does not
        coordinate limits across multiple processes or machines.
      - The burst_allowance field in RateLimitConfig can be used to implement
        short bursts, but is not actively enforced in the current logic.

    Example:
        config = RateLimitConfig(requests_per_minute=120, requests_per_second=2.0)
        rate_limiter = RateLimiter(config)
        await rate_limiter.acquire()  # will block/sleep if necessary
    """

    def __init__(self, config: RateLimitConfig):
        """Initialize the RateLimiter.

        Args:
            config: RateLimitConfig instance containing the throttling parameters.
        """
        self.config = config
        self.request_times: List[float] = []
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request.

        This method will block (async sleep) until performing another request
        would not violate the configured rate limits. It enforces both the
        rolling requests-per-minute constraint and a minimum interval derived
        from requests_per_second.

        Behavior:
          - Removes timestamps older than 60 seconds from internal history.
          - If the requests-per-minute limit is reached, sleeps until the
            oldest timestamp exits the 60s window.
          - Ensures at least (1 / requests_per_second) seconds elapsed since
            the last recorded request; if not, sleeps the remaining time.
          - Records the timestamp of the approved request.

        Returns:
            None

        Concurrency:
            Safe to call from multiple coroutines. Internal Lock serializes
            the check-and-record operation to avoid race conditions.
        """
        async with self._lock:
            current_time = time.time()

            # Remove requests older than 1 minute
            cutoff_time = current_time - 60.0
            self.request_times = [t for t in self.request_times if t > cutoff_time]

            # Check requests per minute limit
            if len(self.request_times) >= self.config.requests_per_minute:
                sleep_time = 60.0 - (current_time - self.request_times[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                    await asyncio.sleep(sleep_time)
                    current_time = time.time()

            # Check requests per second limit
            time_since_last = current_time - self.last_request_time
            min_interval = 1.0 / self.config.requests_per_second

            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                await asyncio.sleep(sleep_time)
                current_time = time.time()

            # Record this request
            self.request_times.append(current_time)
            self.last_request_time = current_time