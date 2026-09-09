"""SentinelX Agent configuration loaded from environment variables."""

from enum import StrEnum
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MonitoringMode(StrEnum):
    """Agent monitoring strictness modes.

    MONITOR_ONLY: Observe and log only — no enforcement actions.
    BALANCED: Enforce policies on high/critical sensitivity; log the rest.
    STRICT: Enforce policies on all sensitivity levels.
    """

    MONITOR_ONLY = "MONITOR_ONLY"
    BALANCED = "BALANCED"
    STRICT = "STRICT"


class AgentSettings(BaseSettings):
    """Configuration for the SentinelX endpoint agent.

    Values are loaded from environment variables prefixed with AGENT_
    and/or from a `.env` file in the project root.
    """

    model_config = SettingsConfigDict(
        env_prefix="AGENT_",
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Connection ---
    SERVER_URL: str = "http://localhost:8000"
    DEVICE_ID: str = "dev-endpoint-001"
    API_TOKEN: str = "CHANGE_ME"

    # --- Paths ---
    PROTECTED_PATHS: str = ""
    TRUSTED_PATHS: str = ""

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- Monitoring ---
    MONITORING_MODE: MonitoringMode = MonitoringMode.MONITOR_ONLY

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}, got '{v}'")
        return upper

    @field_validator("SERVER_URL")
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        """Ensure server URL looks reasonable."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"SERVER_URL must start with http:// or https://, got '{v}'")
        return v.rstrip("/")

    @property
    def protected_path_list(self) -> list[Path]:
        """Parse comma-separated protected paths into Path objects."""
        if not self.PROTECTED_PATHS.strip():
            return []
        return [Path(p.strip()) for p in self.PROTECTED_PATHS.split(",") if p.strip()]

    @property
    def trusted_path_list(self) -> list[Path]:
        """Parse comma-separated trusted paths into Path objects."""
        if not self.TRUSTED_PATHS.strip():
            return []
        return [Path(p.strip()) for p in self.TRUSTED_PATHS.split(",") if p.strip()]


def get_agent_settings() -> AgentSettings:
    """Create and return an AgentSettings instance."""
    return AgentSettings()
