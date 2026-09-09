"""Tests for the health check endpoint and configuration."""

from app.config import Settings
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health endpoint returns HTTP 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client: TestClient) -> None:
        """Health endpoint returns all required fields."""
        response = client.get("/api/v1/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "database" in data
        assert "timestamp" in data

    def test_health_service_name(self, client: TestClient) -> None:
        """Health endpoint returns correct service identifier."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["service"] == "sentinelx-backend"

    def test_health_status_ok(self, client: TestClient) -> None:
        """Health endpoint returns ok status when database is reachable."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "healthy"

    def test_health_version_format(self, client: TestClient) -> None:
        """Health endpoint returns a valid version string."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["version"] == "0.1.0"


class TestConfiguration:
    """Tests for application configuration."""

    def test_default_settings(self) -> None:
        """Settings load with safe development defaults."""
        settings = Settings()
        assert settings.APP_NAME == "SentinelX"
        assert settings.ENVIRONMENT in {"development", "staging", "production", "testing"}
        assert settings.LOG_LEVEL in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    def test_cors_origins_parsing(self) -> None:
        """CORS_ORIGINS string is parsed into a list."""
        settings = Settings(CORS_ORIGINS="http://localhost:3000,http://localhost:5173")
        origins = settings.cors_origin_list
        assert isinstance(origins, list)
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins

    def test_invalid_log_level_rejected(self) -> None:
        """Invalid log levels are rejected by validation."""
        import pytest

        with pytest.raises(Exception):
            Settings(LOG_LEVEL="INVALID")

    def test_invalid_environment_rejected(self) -> None:
        """Invalid environment values are rejected by validation."""
        import pytest

        with pytest.raises(Exception):
            Settings(ENVIRONMENT="invalid_env")
