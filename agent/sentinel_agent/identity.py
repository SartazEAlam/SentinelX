"""Device identity management — generation, persistence, and registration."""

import json
import logging
import platform
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from sentinel_agent import __version__

logger = logging.getLogger(__name__)

IDENTITY_FILENAME = "identity.json"


@dataclass
class DeviceIdentity:
    """Persistent device identity for the SentinelX agent."""

    device_id: str = ""
    device_name: str = ""
    hostname: str = ""
    operating_system: str = ""
    os_version: str = ""
    agent_version: str = ""
    token: str = ""
    registered: bool = False

    @property
    def is_registered(self) -> bool:
        """Check if this identity has a valid token from registration."""
        return self.registered and bool(self.token)


class IdentityManager:
    """Manages device identity lifecycle: generate, save, load.

    The identity file is stored at ``<identity_dir>/identity.json`` and
    contains the device UUID, platform metadata, and the auth token
    received during registration.
    """

    def __init__(self, identity_dir: Path) -> None:
        self._dir = identity_dir
        self._identity_file = identity_dir / IDENTITY_FILENAME
        self._identity: DeviceIdentity | None = None

    @property
    def identity(self) -> DeviceIdentity:
        """Return the current identity (raises if not loaded/generated)."""
        if self._identity is None:
            raise RuntimeError("Identity not loaded — call load() or generate() first")
        return self._identity

    def load(self) -> DeviceIdentity:
        """Load identity from disk, or generate a fresh one if missing."""
        if self._identity_file.exists():
            try:
                data = json.loads(self._identity_file.read_text(encoding="utf-8"))
                self._identity = DeviceIdentity(**data)
                logger.info("Loaded device identity: device_id=%s", self._identity.device_id)
                return self._identity
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                logger.warning("Corrupt identity file, regenerating: %s", exc)

        return self.generate()

    def generate(self) -> DeviceIdentity:
        """Generate a new device identity with platform metadata."""
        self._identity = DeviceIdentity(
            device_id=f"agent-{uuid.uuid4().hex[:12]}",
            device_name=f"{platform.node()}-sentinelx",
            hostname=platform.node(),
            operating_system=platform.system(),
            os_version=platform.version(),
            agent_version=__version__,
            token="",
            registered=False,
        )
        logger.info("Generated new device identity: device_id=%s", self._identity.device_id)
        return self._identity

    def save(self) -> None:
        """Persist the current identity to disk."""
        if self._identity is None:
            raise RuntimeError("No identity to save — call generate() first")

        self._dir.mkdir(parents=True, exist_ok=True)
        data = asdict(self._identity)
        self._identity_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Saved identity to %s", self._identity_file)

    def set_token(self, token: str) -> None:
        """Store the authentication token received from registration."""
        if self._identity is None:
            raise RuntimeError("No identity loaded")
        self._identity.token = token
        self._identity.registered = True
        self.save()
        logger.info("Stored registration token for device %s", self._identity.device_id)

    def has_identity_file(self) -> bool:
        """Check if an identity file exists on disk."""
        return self._identity_file.exists()
