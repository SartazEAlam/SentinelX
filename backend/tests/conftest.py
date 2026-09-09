"""Shared test fixtures for backend tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(app)
