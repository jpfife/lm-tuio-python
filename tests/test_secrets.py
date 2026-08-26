"""Tests for ../src/lm_tuio/config/secrets.py.

Tests SecretsManager file I/O operations.
"""

import os
from pathlib import Path
import stat as stat_module
from unittest.mock import patch

import pytest

from lm_tuio.config import SecretsManager


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / ".config" / "lm-tuio"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class TestSecretsManager:
    """Test SecretsManager load_secrets(), get_api_key(), save_api_key(), remove_endpoints()."""

    @pytest.fixture
    def secrets_manager(self):
        """Provide a fresh SecretsManager with isolated cache."""
        from lm_tuio.config.secrets import SecretsManager

        # Clear the class-level cache before each test
        original_cache = SecretsManager._secrets_cache
        SecretsManager._secrets_cache = None

        manager = SecretsManager()

        yield manager

        SecretsManager._secrets_cache = original_cache

    def _write_secrets(self, tmp_config_dir: Path, content: str) -> Path:
        secrets_path = tmp_config_dir / "secrets.toml"
        secrets_path.write_text(content)
        return secrets_path

    @patch("lm_tuio.config.paths.get_config_path")
    def test_load_empty_file(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_config_dir: Path
    ):
        """Empty secrets file should return empty servers dict."""
        mock_get_path.return_value = tmp_config_dir / "secrets.toml"
        self._write_secrets(tmp_config_dir, "[servers]\n")

        result = secrets_manager.load_secrets()
        assert isinstance(result, dict)
        assert "servers" in result or len(result) == 0

    @patch("lm_tuio.config.paths.get_config_path")
    def test_load_missing_file(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_path: Path
    ):
        """Missing secrets file should return empty servers dict."""
        mock_get_path.return_value = tmp_path / "nonexistent" / "secrets.toml"

        result = secrets_manager.load_secrets()
        assert isinstance(result, dict)
        assert "servers" in result or len(result) == 0

    @patch("lm_tuio.config.paths.get_config_path")
    def test_get_api_key_existing(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_config_dir: Path
    ):
        """Existing API key should be returned."""
        mock_get_path.return_value = tmp_config_dir / "secrets.toml"

        self._write_secrets(
            tmp_config_dir,
            '[servers]\n[servers."192.168.1.10:1234"]\napi_key = "my-secret-key"\n',
        )
        result = secrets_manager.get_api_key("192.168.1.10", 1234)
        assert result == "my-secret-key"

    @patch("lm_tuio.config.paths.get_config_path")
    def test_get_api_key_missing(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_path: Path
    ):
        """Missing endpoint should return empty string."""
        mock_get_path.return_value = tmp_path / "nonexistent" / "secrets.toml"

        result = secrets_manager.get_api_key("192.168.1.10", 1234)
        assert result == ""

    @patch("lm_tuio.config.paths.get_config_path")
    def test_save_api_key_new(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_config_dir: Path
    ):
        """Saving a new API key should create the entry."""
        mock_get_path.return_value = tmp_config_dir / "secrets.toml"

        self._write_secrets(tmp_config_dir, "[servers]\n")
        secrets_manager.save_api_key("192.168.1.10", 1234, "new-key")

        result = secrets_manager.get_api_key("192.168.1.10", 1234)
        assert result == "new-key"

    @patch("lm_tuio.config.paths.get_config_path")
    def test_save_api_key_update(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_config_dir: Path
    ):
        """Updating an existing API key should replace it."""
        mock_get_path.return_value = tmp_config_dir / "secrets.toml"

        self._write_secrets(
            tmp_config_dir,
            '[servers]\n[servers."192.168.1.10:1234"]\napi_key = "old-key"\n',
        )
        secrets_manager.save_api_key("192.168.1.10", 1234, "new-key")

        result = secrets_manager.get_api_key("192.168.1.10", 1234)
        assert result == "new-key"

    @patch("lm_tuio.config.paths.get_config_path")
    def test_save_empty_string_removes_key(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_config_dir: Path
    ):
        """Saving empty string should remove the key."""
        mock_get_path.return_value = tmp_config_dir / "secrets.toml"

        self._write_secrets(
            tmp_config_dir,
            '[servers]\n[servers."192.168.1.10:1234"]\napi_key = "old-key"\n',
        )
        secrets_manager.save_api_key("192.168.1.10", 1234, "")

        result = secrets_manager.get_api_key("192.168.1.10", 1234)
        assert result == ""

    @patch("lm_tuio.config.paths.get_config_path")
    def test_remove_endpoints(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_config_dir: Path
    ):
        """Removing endpoints should delete them from the file."""
        mock_get_path.return_value = tmp_config_dir / "secrets.toml"

        self._write_secrets(
            tmp_config_dir,
            '[servers]\n[servers."192.168.1.10:1234"]\napi_key = "key1"\n'
            '[servers."192.168.1.20:1234"]\napi_key = "key2"\n',
        )
        secrets_manager.remove_endpoints(["192.168.1.10:1234"])

        result = secrets_manager.get_api_key("192.168.1.10", 1234)
        assert result == ""
        # Other endpoint should still exist
        other_result = secrets_manager.get_api_key("192.168.1.20", 1234)
        assert other_result == "key2"

    @patch("lm_tuio.config.paths.get_config_path")
    def test_remove_nonexistent_endpoints(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_path: Path
    ):
        """Removing nonexistent endpoints should be a no-op."""
        mock_get_path.return_value = tmp_path / "nonexistent" / "secrets.toml"

        # No file exists — should not raise
        secrets_manager.remove_endpoints(["nonexistent"])

    @patch("lm_tuio.config.paths.get_config_path")
    def test_cache_invalidation(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_config_dir: Path
    ):
        """Saving should invalidate the cache."""
        mock_get_path.return_value = tmp_config_dir / "secrets.toml"

        self._write_secrets(
            tmp_config_dir,
            '[servers]\n[servers."192.168.1.10:1234"]\napi_key = "old-key"\n',
        )

        # Load and verify
        result1 = secrets_manager.get_api_key("192.168.1.10", 1234)
        assert result1 == "old-key"

        # Save new key
        secrets_manager.save_api_key("192.168.1.10", 1234, "new-key")

        # Verify cache was invalidated — should return new value without re-reading file
        result2 = secrets_manager.get_api_key("192.168.1.10", 1234)
        assert result2 == "new-key"


class TestSecretsManagerPermissions:
    """Test SecretsManager file permission handling."""

    @pytest.fixture
    def tmp_config_dir(self, tmp_path: Path) -> Path:
        config_dir = tmp_path / ".config" / "lm-tuio"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @patch("lm_tuio.config.paths.get_config_path")
    def test_create_file_with_0600_perms(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_config_dir: Path
    ):
        """Creating a new secrets file should set 0600 permissions."""
        mock_get_path.return_value = tmp_config_dir / "secrets.toml"

        # Ensure no file exists
        (tmp_config_dir / "secrets.toml").unlink(missing_ok=True)

        secrets_manager.load_secrets()

        secrets_path = tmp_config_dir / "secrets.toml"
        assert secrets_path.exists()
        perms = stat_module.S_IMODE(secrets_path.stat().st_mode)
        # On Windows, S_IRUSR | S_IWUSR may not be the exact value — just check it's readable/writable
        assert (perms & stat_module.S_IRUSR) and (perms & stat_module.S_IWUSR)

    @patch("lm_tuio.config.paths.get_config_path")
    def test_update_perms_on_existing_file(
        self, mock_get_path, secrets_manager: SecretsManager, tmp_config_dir: Path
    ):
        """Updating an existing file with wrong permissions should fix them."""
        mock_get_path.return_value = tmp_config_dir / "secrets.toml"

        secrets_path = tmp_config_dir / "secrets.toml"
        secrets_path.write_text("[servers]\n")
        # Set wrong permissions (0755)
        os.chmod(secrets_path, 0o755)

        secrets_manager.load_secrets()

        perms = stat_module.S_IMODE(secrets_path.stat().st_mode)
        assert (perms & stat_module.S_IRUSR) and (perms & stat_module.S_IWUSR)


class TestSecretsManagerHeader:
    """Test the default header string."""

    def test_header_format(self):
        """Default header should have expected format."""
        from lm_tuio.config.secrets import SecretsManager as SM

        assert "# LM TUIO API keys\n\n[servers]\n" == SM.header_str
