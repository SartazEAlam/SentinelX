"""Tests for device identity management."""

from pathlib import Path

from sentinel_agent.identity import DeviceIdentity, IdentityManager


class TestDeviceIdentity:
    """Tests for the DeviceIdentity dataclass."""

    def test_default_not_registered(self) -> None:
        """New identity is not registered by default."""
        identity = DeviceIdentity()
        assert not identity.is_registered

    def test_registered_with_token(self) -> None:
        """Identity with token and registered flag is registered."""
        identity = DeviceIdentity(token="abc123", registered=True)
        assert identity.is_registered

    def test_not_registered_without_flag(self) -> None:
        """Token alone doesn't count — registered flag must be True."""
        identity = DeviceIdentity(token="abc123", registered=False)
        assert not identity.is_registered


class TestIdentityManager:
    """Tests for identity generation, save, and load."""

    def test_generate_creates_identity(self, tmp_path: Path) -> None:
        """Generate produces a valid device identity."""
        mgr = IdentityManager(tmp_path / ".sentinelx")
        identity = mgr.generate()
        assert identity.device_id.startswith("agent-")
        assert len(identity.device_id) > 6
        assert identity.hostname != ""
        assert identity.operating_system != ""
        assert not identity.is_registered

    def test_save_and_load(self, tmp_path: Path) -> None:
        """Identity can be saved and loaded from disk."""
        dir_path = tmp_path / ".sentinelx"
        mgr = IdentityManager(dir_path)
        original = mgr.generate()
        mgr.save()

        # Load in a new manager
        mgr2 = IdentityManager(dir_path)
        loaded = mgr2.load()

        assert loaded.device_id == original.device_id
        assert loaded.hostname == original.hostname
        assert loaded.operating_system == original.operating_system

    def test_set_token_persists(self, tmp_path: Path) -> None:
        """set_token saves the token and marks as registered."""
        dir_path = tmp_path / ".sentinelx"
        mgr = IdentityManager(dir_path)
        mgr.generate()
        mgr.set_token("secret-token-xyz")

        # Reload
        mgr2 = IdentityManager(dir_path)
        loaded = mgr2.load()

        assert loaded.is_registered
        assert loaded.token == "secret-token-xyz"

    def test_load_generates_if_no_file(self, tmp_path: Path) -> None:
        """Load generates a new identity if no file exists."""
        mgr = IdentityManager(tmp_path / ".sentinelx")
        identity = mgr.load()
        assert identity.device_id.startswith("agent-")
        assert not identity.is_registered

    def test_corrupt_file_regenerates(self, tmp_path: Path) -> None:
        """Corrupt identity file triggers regeneration."""
        dir_path = tmp_path / ".sentinelx"
        dir_path.mkdir(parents=True)
        (dir_path / "identity.json").write_text("not valid json", encoding="utf-8")

        mgr = IdentityManager(dir_path)
        identity = mgr.load()
        assert identity.device_id.startswith("agent-")

    def test_has_identity_file(self, tmp_path: Path) -> None:
        """has_identity_file reflects file existence."""
        dir_path = tmp_path / ".sentinelx"
        mgr = IdentityManager(dir_path)

        assert not mgr.has_identity_file()

        mgr.generate()
        mgr.save()

        assert mgr.has_identity_file()
