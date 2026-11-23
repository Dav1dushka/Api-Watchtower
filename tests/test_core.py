import pytest

from app.core import assess_response, validate_target_url


def test_validate_https_url():
    assert validate_target_url(" https://example.com/health ") == "https://example.com/health"


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com",
        "example.com",
        "https://user:pass@example.com",
        "https://",
        "https://exa mple.com",
        "https://example.com:invalid",
    ],
)
def test_rejects_invalid_urls(url):
    with pytest.raises(ValueError):
        validate_target_url(url)


def test_https_header_score():
    result = assess_response(
        200,
        {
            "strict-transport-security": "max-age=31536000",
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
        },
        "https",
    )
    assert result["health"] == "DEGRADED"
    assert result["security_score"] == 55
    assert "content-security-policy" in result["missing_headers"]


def test_http_does_not_require_hsts():
    result = assess_response(200, {}, "http")
    assert "strict-transport-security" not in result["missing_headers"]
    assert result["security_score"] == 25


def test_complete_https_headers_score_one_hundred():
    result = assess_response(
        200,
        {
            "strict-transport-security": "max-age=31536000",
            "content-security-policy": "default-src 'self'",
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
            "referrer-policy": "strict-origin-when-cross-origin",
            "permissions-policy": "camera=(), microphone=()",
        },
        "https",
    )
    assert result["health"] == "HEALTHY"
    assert result["security_score"] == 100


def test_server_error_is_down():
    result = assess_response(503, {}, "https")
    assert result["health"] == "DOWN"
    assert result["security_score"] == 0


def test_connection_error_is_down():
    result = assess_response(None, {}, "https", "Connection error")
    assert result["health"] == "DOWN"
    assert result["error"] == "Connection error"
