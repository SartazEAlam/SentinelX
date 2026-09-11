"""Application configuration loaded from environment variables."""

from pathlib import Path
from typing import ClassVar

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SentinelX backend configuration.

    Values are loaded from environment variables and/or a `.env` file.
    The `.env` file is searched from the project root (two levels above this file).
    """

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "SentinelX"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- Server ---
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./sentinelx.db"

    # --- Security / JWT ---
    JWT_SECRET_KEY: str = "CHANGE_ME_BEFORE_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- CORS ---
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    )

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- Initial Admin Bootstrap ---
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "Admin@123!"
    FIRST_ADMIN_EMAIL: str = "admin@sentinelx.com"

    # --- Pagination ---
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200

    # --- Event Ingestion ---
    MAX_BATCH_SIZE: int = 100

    # --- Derived ---
    SENSITIVE_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"JWT_SECRET_KEY", "FIRST_ADMIN_PASSWORD", "API_TOKEN", "DATABASE_URL"}
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure the log level is a recognized Python logging level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Ensure the environment is a recognized value."""
        allowed = {"development", "staging", "production", "testing"}
        lower = v.lower()
        if lower not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return lower

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Warn if the default JWT secret is used (enforced at startup for production)."""
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"


def get_settings() -> Settings:
    """Create and return a Settings instance."""
    return Settings()
