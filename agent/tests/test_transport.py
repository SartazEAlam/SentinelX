"""Tests for HTTP transport."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sentinel_agent.transport.http_transport import HTTPTransport, TransportResult


class TestTransportResult:
    """Tests for TransportResult dataclass."""

    def test_success_result(self) -> None:
        """Successful result has correct attributes."""
        result = TransportResult(success=True, status_code=200, data={"id": 1})
        assert result.success
        assert result.status_code == 200
        assert result.data == {"id": 1}

    def test_failure_result(self) -> None:
        """Failed result has error message."""
        result = TransportResult(success=False, error="connection refused")
        assert not result.success
        assert result.error == "connection refused"


class TestHTTPTransport:
    """Tests for HTTPTransport."""

    def test_init_strips_trailing_slash(self) -> None:
        """Server URL trailing slash is stripped."""
        transport = HTTPTransport(server_url="http://localhost:8000/")
        assert transport._server_url == "http://localhost:8000"

    def test_set_token(self) -> None:
        """Token can be updated after init."""
        transport = HTTPTransport(server_url="http://localhost:8000")
        assert transport.token == ""
        transport.set_token("new-token")
        assert transport.token == "new-token"

    @pytest.mark.asyncio
    async def test_register_device_success(self) -> None:
        """Register device returns success with token."""
        transport = HTTPTransport(server_url="http://localhost:8000", max_retries=1)

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1,
            "device_id": "agent-abc",
            "token": "device-token-xyz",
            "status": "UNKNOWN",
            "registered_at": "2026-01-01T00:00:00Z",
        }

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        transport._client = mock_client

        result = await transport.register_device({
            "device_id": "agent-abc",
            "device_name": "test-device",
        })

        assert result.success
        assert result.data["token"] == "device-token-xyz"

    @pytest.mark.asyncio
    async def test_send_heartbeat_success(self) -> None:
        """Heartbeat returns success."""
        transport = HTTPTransport(
            server_url="http://localhost:8000",
            token="test-token",
            max_retries=1,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"device_id": "agent-abc", "status": "ONLINE"}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        transport._client = mock_client

        result = await transport.send_heartbeat({"agent_version": "0.2.0"})
        assert result.success

    @pytest.mark.asyncio
    async def test_send_event_failure(self) -> None:
        """Event send failure returns error."""
        transport = HTTPTransport(
            server_url="http://localhost:8000",
            token="test-token",
            max_retries=1,
        )

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        transport._client = mock_client

        result = await transport.send_event({"event_id": "evt-1"})
        assert not result.success
        assert "500" in result.error

    @pytest.mark.asyncio
    async def test_client_error_no_retry(self) -> None:
        """4xx errors are not retried."""
        transport = HTTPTransport(
            server_url="http://localhost:8000",
            token="test-token",
            max_retries=3,
        )

        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Unprocessable Entity"

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        transport._client = mock_client

        result = await transport.send_event({"event_id": "evt-1"})
        assert not result.success
        # Should only have been called once (no retries for 4xx)
        assert mock_client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Close clears the client."""
        transport = HTTPTransport(server_url="http://localhost:8000")
        mock_client = AsyncMock()
        mock_client.is_closed = False
        transport._client = mock_client

        await transport.close()
        mock_client.aclose.assert_called_once()
        assert transport._client is None
