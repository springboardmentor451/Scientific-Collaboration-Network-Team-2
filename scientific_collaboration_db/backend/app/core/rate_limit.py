"""
A deliberately simple, in-process rate limiter for the authentication
endpoints (password login, OTP verification/resend). It is NOT a
distributed rate limiter — state lives in this process's memory, so it
resets on restart and isn't shared across multiple backend workers. That's
an acceptable tradeoff for a single-instance deployment and a large
improvement over having no limiting at all; a production deployment running
multiple workers behind a load balancer should replace this with a shared
store (e.g. Redis) using the same key scheme.
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

# key -> deque of unix timestamps for recent attempts
_attempts: dict[str, deque] = defaultdict(deque)


def _prune(key: str, window_seconds: int) -> deque:
    bucket = _attempts[key]
    cutoff = time.time() - window_seconds
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    return bucket


def check_rate_limit(key: str, *, max_attempts: int, window_seconds: int) -> None:
    """
    Raises 429 if `key` has already made `max_attempts` or more calls within
    the trailing `window_seconds`. Call this BEFORE doing the expensive/
    sensitive work (password check, OTP check), then call `record_attempt`
    once the attempt has actually been made, successful or not — failed
    attempts count too, since those are exactly what this is meant to slow
    down (credential stuffing, OTP brute-forcing).
    """
    bucket = _prune(key, window_seconds)
    if len(bucket) >= max_attempts:
        retry_after = int(window_seconds - (time.time() - bucket[0])) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


def record_attempt(key: str) -> None:
    _attempts[key].append(time.time())
