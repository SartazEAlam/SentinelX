"""HTTP transport — async communication with the SentinelX backend."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class TransportResult:
    """Result of an HTTP transport operation."""

    success: bool
    status_code: int = 0
    data: dict[str, Any] | None = None
    error: str = ""


class HTTPTransport:
    """Async HTTP client for SentinelX backend communication.

    Handles device registration, heartbeat, and event ingestion with
    configurable retry and exponential backoff.
    """

    def __init__(
        self,
        server_url: str,
        token: str = "",
        max_retries: int = 3,
        backoff_seconds: float = 5.0,
        timeout: float = 30.0,
    ) -> None:
        self._server_url = server_url.rstrip("/")
        self._token = token
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def token(self) -> str:
        """Current authentication token."""
        return self._token

    def set_token(self, token: str) -> None:
        """Update the authentication token (after registration)."""
        self._token = token
        # Recreate client headers on next request
        if self._client is not None:
            self._client.headers["Authorization"] = f"Bearer {token}"

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Create or return the HTTP client."""
        if self._client is None or self._client.is_closed:
            headers: dict[str, str] = {
                "Content-Type": "application/json",
                "User-Agent": "SentinelX-Agent/0.2.0",
            }
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            self._client = httpx.AsyncClient(
                base_url=self._server_url,
                headers=headers,
                timeout=httpx.Timeout(self._timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
        retry: bool = True,
    ) -> TransportResult:
        """Execute an HTTP request with optional retry and backoff."""
        max_attempts = self._max_retries if retry else 1
        last_error = ""

        for attempt in range(1, max_attempts + 1):
            try:
                client = await self._ensure_client()
                response = await client.request(method, path, json=json_data)

                if response.status_code < 400:
                    try:
                        data = response.json()
                    except Exception:
                        data = None
                    return TransportResult(
                        success=True,
                        status_code=response.status_code,
                        data=data,
                    )

                # Client/server error
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                if response.status_code < 500:
                    # Don't retry client errors (4xx)
                    return TransportResult(
                        success=False,
                        status_code=response.status_code,
                        error=last_error,
                    )

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            except Exception as exc:
                last_error = f"Unexpected error: {exc}"

            if attempt < max_attempts:
                wait = self._backoff_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "Request %s %s failed (attempt %d/%d): %s — retrying in %.1fs",
                    method, path, attempt, max_attempts, last_error, wait,
                )
                await asyncio.sleep(wait)

        logger.error(
            "Request %s %s failed after %d attempts: %s",
            method, path, max_attempts, last_error,
        )
        return TransportResult(success=False, error=last_error)

    # ── Public API ──────────────────────────────────────────────────

    async def is_server_reachable(self) -> bool:
        """Check if the backend is reachable via the health endpoint."""
        result = await self._request_with_retry("GET", "/api/v1/health", retry=False)
        return result.success

    async def register_device(self, registration_data: dict[str, Any]) -> TransportResult:
        """Register this device with the backend.

        POST /api/v1/devices/register
        """
        logger.info("Registering device with backend...")
        return await self._request_with_retry(
            "POST", "/api/v1/devices/register", json_data=registration_data
        )

    async def send_heartbeat(self, heartbeat_data: dict[str, Any]) -> TransportResult:
        """Send a heartbeat to the backend.

        POST /api/v1/devices/heartbeat
        """
        return await self._request_with_retry(
            "POST", "/api/v1/devices/heartbeat", json_data=heartbeat_data
        )

    async def send_event(self, event_data: dict[str, Any]) -> TransportResult:
        """Send a single security event.

        POST /api/v1/events
        """
        return await self._request_with_retry(
            "POST", "/api/v1/events", json_data=event_data
        )

    async def send_events_batch(self, events: list[dict[str, Any]]) -> TransportResult:
        """Send a batch of security events.

        POST /api/v1/events/batch
        """
        return await self._request_with_retry(
            "POST", "/api/v1/events/batch", json_data={"events": events}
        )
