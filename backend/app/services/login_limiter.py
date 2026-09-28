from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status

MAX_ATTEMPTS = 5
WINDOW = timedelta(minutes=15)
_attempts: dict[str, deque[datetime]] = defaultdict(deque)


def enforce_login_rate_limit(request: Request, email: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{email.strip().lower()}"
    now = datetime.now(UTC)
    attempts = _attempts[key]
    while attempts and attempts[0] <= now - WINDOW:
        attempts.popleft()
    if len(attempts) >= MAX_ATTEMPTS:
        retry_after = int((attempts[0] + WINDOW - now).total_seconds()) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    return key


def record_failed_login(key: str) -> None:
    _attempts[key].append(datetime.now(UTC))


def clear_login_attempts(key: str) -> None:
    _attempts.pop(key, None)
