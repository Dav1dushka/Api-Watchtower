from __future__ import annotations

import time
from urllib.parse import urlparse

import httpx

from .core import assess_response


async def check_url(url: str) -> dict:
    """
    Make one ordinary GET request to a manually added endpoint.
    Redirects are deliberately not followed.
    """
    parsed = urlparse(url)
    started = time.perf_counter()

    try:
        timeout = httpx.Timeout(8.0, connect=5.0)
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            headers={"User-Agent": "API-Watchtower/1.0"},
        ) as client:
            response = await client.get(url)

        return {
            "status_code": response.status_code,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            **assess_response(response.status_code, dict(response.headers), parsed.scheme),
        }
    except httpx.TimeoutException:
        return {
            "status_code": None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            **assess_response(None, {}, parsed.scheme, "Request timed out"),
        }
    except httpx.RequestError as exc:
        return {
            "status_code": None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            **assess_response(
                None, {}, parsed.scheme, f"Connection error: {type(exc).__name__}"
            ),
        }
