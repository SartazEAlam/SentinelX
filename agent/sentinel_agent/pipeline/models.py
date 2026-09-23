"""Normalised event model — the agent's internal event representation."""

import os
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from sentinel_agent.classification.result import ClassificationResult


class EndpointEvent(BaseModel):
    """A normalised security event produced by a collector.

    This is the agent's canonical event format. The ``to_api_dict()``
    method converts it to the payload expected by the backend's
    ``SecurityEventCreate`` schema.
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: str = "OTHER"
    action: str = ""
    source: str = ""
    destination: str = ""
    file_name: str = ""
    file_path: str = ""
    file_size: int | None = None
    file_hash: str | None = None
    process_name: str = ""
    process_id: int | None = None
    user_context: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    classification: ClassificationResult | None = None

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to the backend ``SecurityEventCreate``-compatible dict."""
        data: dict[str, Any] = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
        }
        # Only include optional fields that have values
        if self.action:
            data["action"] = self.action
        if self.source:
            data["source"] = self.source
        if self.destination:
            data["destination"] = self.destination
        if self.file_name:
            data["file_name"] = self.file_name
        if self.file_path:
            data["file_path"] = self.file_path
        if self.file_size is not None:
            data["file_size"] = self.file_size
        if self.file_hash:
            data["file_hash"] = self.file_hash
        if self.process_name:
            data["process_name"] = self.process_name
        if self.process_id is not None:
            data["process_id"] = self.process_id
        if self.user_context:
            data["user_context"] = self.user_context
        if self.metadata:
            data["metadata_json"] = self.metadata
        if self.classification:
            data["classification"] = self.classification.to_api_dict()
            # Also set sensitivity_level at top level for backward compat or direct querying
            data["sensitivity_level"] = self.classification.sensitivity_level.value
        return data


def get_current_user() -> str:
    """Get the current OS username, safely."""
    try:
        return os.getlogin()
    except OSError:
        try:
            import getpass

            return getpass.getuser()
        except Exception:
            return "unknown"
