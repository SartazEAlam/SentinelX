"""Pytest configuration and fixtures for SentinelX."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set test environment config
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test_super_secret_key"

from app.config import get_settings
from app.db.base import Base
from app.db.database import get_db
from app.main import app
from app.models.enums import UserRole
from app.schemas.users import UserCreate
from app.services.auth_service import create_initial_admin_if_needed
from app.services.user_service import create_user

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Create all tables in the test database before tests run."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Bootstrap initial admin
    with TestingSessionLocal() as db:
        create_initial_admin_if_needed(db)

    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provide a fresh database session for a test."""
    # We could wrap tests in transactions for rollback, but for simplicity
    # with SQLite we'll just yield a session. In a larger suite we'd clear tables.
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient with the database dependency overridden."""
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client: TestClient, db: Session) -> str:
    """Provide an access token for the admin user."""
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.FIRST_ADMIN_USERNAME,
            "password": settings.FIRST_ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def viewer_token(client: TestClient, db: Session) -> str:
    """Provide an access token for a viewer user."""
    # Create a viewer user if it doesn't exist
    user_in = UserCreate(
        username="test_viewer",
        password="ViewerPassword123!",
        email="viewer@test.com",
        full_name="Test Viewer",
        role=UserRole.VIEWER,
    )
    # create_user will raise if user exists, so handle gracefully or just create in the transaction
    # Since tests run in isolated transactions, we should create it here.
    create_user(db, user_in)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test_viewer",
            "password": "ViewerPassword123!",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]
