"""
Tests for RateLimitMiddleware.

The middleware being tested lives at backend/middleware/rate_limit.py and is
expected to:
  - Track requests per IP using an in-memory sliding window.
  - Default to 100 requests per 60-second window, but accept constructor args
    `requests_per_window` and `window_seconds`.
  - Return HTTP 429 with a JSON body when the limit is exceeded.
  - Include X-RateLimit-Limit, X-RateLimit-Remaining, and X-RateLimit-Reset
    headers on every response.

A minimal FastAPI app is constructed in this module so the tests are fully
self-contained and do not depend on the real application's database or external
services.
"""

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.middleware.rate_limit import RateLimitMiddleware

SMALL_LIMIT = 5        # requests allowed per window
SMALL_WINDOW = 1       # window size in seconds (kept tiny for reset tests)


def build_app(requests_per_window: int = SMALL_LIMIT, window_seconds: int = SMALL_WINDOW) -> FastAPI:
    """Return a minimal FastAPI app with RateLimitMiddleware attached."""
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_window=requests_per_window,
        window_seconds=window_seconds,
    )

    @app.get("/ping")
    async def ping():
        return {"message": "pong"}

    return app


@pytest.fixture()
def client() -> TestClient:
    """TestClient backed by a fresh app instance for each test."""
    return TestClient(build_app(), raise_server_exceptions=True)


class TestRequestsUnderLimit:
    def test_all_requests_within_limit_return_200(self, client: TestClient):
        """Every request up to the limit should return 200 OK."""
        for i in range(SMALL_LIMIT):
            response = client.get("/ping")
            assert response.status_code == 200, (
                f"Request {i + 1}/{SMALL_LIMIT} unexpectedly returned {response.status_code}"
            )

    def test_response_body_is_intact(self, client: TestClient):
        """A successful response should contain the expected JSON body."""
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"message": "pong"}


class TestRequestsOverLimit:
    def test_request_exceeding_limit_returns_429(self, client: TestClient):
        """The (limit + 1)th request within the window must return 429."""
        for _ in range(SMALL_LIMIT):
            client.get("/ping")

        response = client.get("/ping")
        assert response.status_code == 429

    def test_429_response_has_json_body(self, client: TestClient):
        """The 429 response must include a JSON body (not an empty body)."""
        for _ in range(SMALL_LIMIT):
            client.get("/ping")

        response = client.get("/ping")
        assert response.status_code == 429
        body = response.json()
        assert isinstance(body, dict), "429 body should be a JSON object"
        body_text = str(body).lower()
        assert any(
            keyword in body_text for keyword in ("rate", "limit", "too many")
        ), f"429 body does not describe a rate limit error: {body}"


class TestRateLimitHeaders:
    REQUIRED_HEADERS = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ]

    def test_headers_present_on_successful_response(self, client: TestClient):
        """Rate limit headers must be included on every 200 response."""
        response = client.get("/ping")
        assert response.status_code == 200
        for header in self.REQUIRED_HEADERS:
            assert header in response.headers, f"Missing header: {header}"

    def test_headers_present_on_429_response(self, client: TestClient):
        """Rate limit headers must also be included on 429 responses."""
        for _ in range(SMALL_LIMIT):
            client.get("/ping")
        response = client.get("/ping")
        assert response.status_code == 429
        for header in self.REQUIRED_HEADERS:
            assert header in response.headers, f"Missing header on 429: {header}"

    def test_limit_header_matches_configured_limit(self, client: TestClient):
        """X-RateLimit-Limit should reflect the configured requests_per_window."""
        response = client.get("/ping")
        assert int(response.headers["X-RateLimit-Limit"]) == SMALL_LIMIT

    def test_remaining_decrements_with_each_request(self, client: TestClient):
        """X-RateLimit-Remaining should count down as requests are consumed."""
        previous_remaining = None
        for _ in range(SMALL_LIMIT):
            response = client.get("/ping")
            current_remaining = int(response.headers["X-RateLimit-Remaining"])
            if previous_remaining is not None:
                assert current_remaining == previous_remaining - 1, (
                    "X-RateLimit-Remaining did not decrement by 1"
                )
            previous_remaining = current_remaining

    def test_remaining_is_zero_or_below_when_limit_hit(self, client: TestClient):
        """After exhausting the limit, X-RateLimit-Remaining should be 0."""
        for _ in range(SMALL_LIMIT):
            client.get("/ping")
        response = client.get("/ping")
        assert response.status_code == 429
        remaining = int(response.headers["X-RateLimit-Remaining"])
        assert remaining == 0

    def test_reset_header_is_a_positive_unix_timestamp(self, client: TestClient):
        """X-RateLimit-Reset should be a Unix timestamp in the future."""
        response = client.get("/ping")
        reset_ts = float(response.headers["X-RateLimit-Reset"])
        assert reset_ts > time.time(), (
            "X-RateLimit-Reset should be a future Unix timestamp"
        )


class TestPerIpIsolation:
    def test_different_ips_do_not_share_quota(self):
        """Exhausting the limit for one IP must not affect a different IP."""
        app = build_app()
        client_a = TestClient(app, headers={"X-Forwarded-For": "10.0.0.1"})
        client_b = TestClient(app, headers={"X-Forwarded-For": "10.0.0.2"})

        for _ in range(SMALL_LIMIT):
            client_a.get("/ping")
        over_limit_response = client_a.get("/ping")
        assert over_limit_response.status_code == 429, (
            "IP A should be rate limited after exhausting its quota"
        )

        response_b = client_b.get("/ping")
        assert response_b.status_code == 200, (
            "IP B should not be rate limited by IP A's quota consumption"
        )

    def test_each_ip_gets_full_limit(self):
        """Each unique IP should independently receive the full request quota."""
        app = build_app()

        for ip_suffix in range(1, 4):
            ip = f"192.168.1.{ip_suffix}"
            ip_client = TestClient(app, headers={"X-Forwarded-For": ip})
            for i in range(SMALL_LIMIT):
                response = ip_client.get("/ping")
                assert response.status_code == 200, (
                    f"IP {ip}: request {i + 1} returned {response.status_code}, "
                    "expected 200"
                )


class TestWindowReset:
    def test_quota_is_restored_after_window_expires(self):
        """
        After the sliding window elapses, the IP's counter should reset and
        new requests should succeed again.

        We use a 1-second window so the test completes quickly.
        """
        app = build_app(requests_per_window=SMALL_LIMIT, window_seconds=1)
        client = TestClient(app, raise_server_exceptions=True)

        for _ in range(SMALL_LIMIT):
            client.get("/ping")
        assert client.get("/ping").status_code == 429, (
            "Should be rate limited before window reset"
        )

        # Small buffer for timing jitter beyond the 1s window.
        time.sleep(1.1)

        response = client.get("/ping")
        assert response.status_code == 200, (
            "Request should succeed after the rate limit window has expired"
        )

    def test_remaining_resets_to_full_after_window(self):
        """After a window reset, X-RateLimit-Remaining should return to its max value."""
        app = build_app(requests_per_window=SMALL_LIMIT, window_seconds=1)
        client = TestClient(app, raise_server_exceptions=True)

        for _ in range(SMALL_LIMIT):
            client.get("/ping")

        time.sleep(1.1)

        response = client.get("/ping")
        assert response.status_code == 200
        remaining = int(response.headers["X-RateLimit-Remaining"])
        assert remaining == SMALL_LIMIT - 1, (
            f"Expected remaining={SMALL_LIMIT - 1} after window reset, got {remaining}"
        )
