from __future__ import annotations

from urllib.parse import urlparse

# Weights add up to 100 for HTTPS endpoints.
HEADER_WEIGHTS = {
    "strict-transport-security": 25,
    "content-security-policy": 25,
    "x-content-type-options": 15,
    "x-frame-options": 15,
    "referrer-policy": 10,
    "permissions-policy": 10,
}


def validate_target_url(value: str) -> str:
    """Validate an HTTP(S) endpoint supplied by the local dashboard user."""
    value = value.strip()
    parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http:// and https:// URLs are supported.")
    if not parsed.hostname:
        raise ValueError("The URL must contain a hostname.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed.")
    if any(char.isspace() for char in value):
        raise ValueError("The URL cannot contain whitespace.")
    if len(value) > 2048:
        raise ValueError("The URL is too long.")

    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("The URL contains an invalid port.") from exc

    return value


def assess_response(
    status_code: int | None,
    headers: dict[str, str] | None,
    scheme: str,
    error: str | None = None,
) -> dict:
    """Return availability state and a transparent header-presence score."""
    normalized = {
        str(key).lower(): str(value).strip()
        for key, value in (headers or {}).items()
    }
    required = dict(HEADER_WEIGHTS)

    # HSTS only applies to HTTPS endpoints.
    if scheme.lower() != "https":
        required.pop("strict-transport-security", None)

    missing = [name for name in required if not normalized.get(name)]
    score = 100 - sum(required[name] for name in missing)

    if error:
        health = "DOWN"
        score = 0
    elif status_code is None:
        health = "UNKNOWN"
        score = 0
    elif status_code >= 500:
        health = "DOWN"
        score = 0
    elif status_code >= 400:
        health = "DEGRADED"
    elif missing:
        health = "DEGRADED"
    else:
        health = "HEALTHY"

    return {
        "health": health,
        "security_score": max(0, min(100, score)),
        "missing_headers": missing,
        "error": error,
    }
