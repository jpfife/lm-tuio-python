"""Tests for ../src/lm_tuio/config/settings.py.

Tests validate_port(), AppConfig.load/save, _parse_toml, _resolve_config_file.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import tomlkit

from lm_tuio.config.settings import validate_port


# ===== validate_port =====


class TestValidatePort:
    """Test port validation for valid range (1–65535)."""

    def test_port_one(self):
        """Minimum valid port."""
        err, sev = validate_port(1)
        assert err is None
        assert sev is None

    def test_port_sixty_five_thousand_three_five(self):
        """Maximum valid port."""
        err, sev = validate_port(65535)
        assert err is None
        assert sev is None

    def test_port_zero(self):
        """Below minimum."""
        err, sev = validate_port(0)
        assert err is not None
        assert sev == "error"

    def test_port_sixty_five_thousand_six_three_five(self):
        """Above maximum."""
        err, sev = validate_port(65536)
        assert err is not None
        assert sev == "error"

    def test_port_negative(self):
        """Negative port."""
        err, sev = validate_port(-1)
        assert err is not None
        assert sev == "error"

    def test_port_string_valid(self):
        """String that parses to valid int."""
        err, sev = validate_port("8080")
        assert err is None
        assert sev is None

    def test_port_string_invalid(self):
        """Non-numeric string."""
        err, sev = validate_port("abc")
        assert err is not None
        assert sev == "error"

    def test_port_string_zero(self):
        """String '0'."""
        err, sev = validate_port("0")
        assert err is not None
        assert sev == "error"

    def test_port_string_over_max(self):
        """String above max."""
        err, sev = validate_port("99999")
        assert err is not None
        assert sev == "error"

    def test_port_empty_string(self):
        """Empty string."""
        err, sev = validate_port("")
        assert err is not None
        assert sev == "error"


# ===== AppConfig._resolve_config_file =====


class TestResolveConfigFile:
    """Test _resolve_config_file path resolution."""

    def test_resolves_file_directly(self, tmp_path: Path):
        """If config_path points to a file, return it as-is."""
        cfg_file = tmp_path / "my_config.toml"
        cfg_file.write_text("[server]\n")
        from lm_tuio.config.settings import AppConfig

        ac = AppConfig(config_path=str(cfg_file))
        resolved = ac._resolve_config_file()
        assert resolved == cfg_file

    def test_resolves_directory_appends_config(self, tmp_path: Path):
        """If config_path is a directory, append config.toml."""
        cfg_dir = tmp_path / "config_dir"
        cfg_dir.mkdir()
        from lm_tuio.config.settings import AppConfig

        ac = AppConfig(config_path=str(cfg_dir))
        resolved = ac._resolve_config_file()
        assert resolved == cfg_dir / "config.toml"

    def test_creates_missing_directory(self, tmp_path: Path):
        """Non-existent directory is created."""
        deep = tmp_path / "a" / "b" / "c"
        from lm_tuio.config.settings import AppConfig

        ac = AppConfig(config_path=str(deep))
        resolved = ac._resolve_config_file()
        assert deep.exists()
        assert resolved == deep / "config.toml"

    def test_resolves_nonexistent_file_with_suffix(self, tmp_path: Path):
        """Non-existent file path (with suffix) creates parent dirs, returns file path — not a directory."""
        cfg_file = tmp_path / "lm-tuio" / "config.toml"
        from lm_tuio.config.settings import AppConfig

        ac = AppConfig(config_path=str(cfg_file))
        resolved = ac._resolve_config_file()

        assert (tmp_path / "lm-tuio").exists()  # parent dir created
        assert resolved == cfg_file
        assert not cfg_file.exists()  # file not created yet
        assert not cfg_file.is_dir()  # definitely not a directory


# ===== AppConfig._parse_toml =====


class TestParseToml:
    """Test _parse_toml reading and parsing."""

    def test_parses_valid_config(self, tmp_path: Path):
        """Valid TOML returns updates dict and no error."""
        cfg = tmp_path / "config.toml"
        cfg.write_text(
            '[server]\ndefault_ip = "10.0.0.1"\ndefault_port = 8080\n'
            '[app]\ntheme = "textual-dracula"\n'
        )
        from lm_tuio.config.settings import AppConfig

        updates, err = AppConfig._parse_toml(cfg)
        assert err is None
        assert updates["target"] == "10.0.0.1"
        assert updates["port"] == 8080
        assert updates["theme"] == "textual-dracula"

    def test_parses_missing_sections(self, tmp_path: Path):
        """TOML with only one section returns only that section's fields."""
        cfg = tmp_path / "config.toml"
        cfg.write_text('[server]\ndefault_ip = "10.0.0.1"\n')
        from lm_tuio.config.settings import AppConfig

        updates, err = AppConfig._parse_toml(cfg)
        assert err is None
        assert "target" in updates
        assert "port" not in updates  # not in TOML

    def test_parses_empty_file(self, tmp_path: Path):
        """Empty file returns empty updates, no error."""
        cfg = tmp_path / "config.toml"
        cfg.write_text("")
        from lm_tuio.config.settings import AppConfig

        updates, err = AppConfig._parse_toml(cfg)
        assert err is None
        assert updates == {}

    def test_parses_malformed_toml(self, tmp_path: Path):
        """Malformed TOML returns error message, empty updates."""
        cfg = tmp_path / "config.toml"
        cfg.write_text("[server\ndefault_ip = \"bad\"\n")
        from lm_tuio.config.settings import AppConfig

        updates, err = AppConfig._parse_toml(cfg)
        assert err is not None
        assert "Error reading config.toml" in err
        assert updates == {}

    def test_parses_nonexistent_file(self, tmp_path: Path):
        """Non-existent file returns error."""
        cfg = tmp_path / "nope.toml"
        from lm_tuio.config.settings import AppConfig

        updates, err = AppConfig._parse_toml(cfg)
        assert err is not None
        assert updates == {}


# ===== AppConfig.load =====


class TestAppConfigLoad:
    """Test AppConfig.load hierarchical loading."""

    def _make_cfg_dir(self, tmp_path: Path, content: str | None = None) -> Path:
        """Create a temp config directory with optional TOML content."""
        cfg_dir = tmp_path / ".config" / "lm-tuio"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        if content is not None:
            (cfg_dir / "config.toml").write_text(content)
        return cfg_dir

    def test_load_defaults_only(self, tmp_path: Path):
        """No config.toml → defaults + creates file."""
        cfg_dir = self._make_cfg_dir(tmp_path)
        from lm_tuio.config.settings import AppConfig

        with patch(
            "lm_tuio.config.settings.paths.get_config_path",
            return_value=cfg_dir / "config.toml",
        ):
            config, status = AppConfig.load()

        assert config is not None
        assert config.target == "127.0.0.1"
        assert config.port == 1234
        assert config.scan_subnet == "192.168.1.0/24"
        assert config.theme == "textual-dark"
        assert "config.toml not found" in status

    def test_load_overrides_from_toml(self, tmp_path: Path):
        """config.toml values override defaults."""
        cfg_dir = self._make_cfg_dir(
            tmp_path,
            '[server]\ndefault_ip = "10.0.0.5"\ndefault_port = 9999\n'
            '[app]\ntheme = "textual-nord"\n',
        )
        from lm_tuio.config.settings import AppConfig

        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=cfg_dir / "config.toml",
        ):
            config, status = AppConfig.load()

        assert config is not None
        assert config.target == "10.0.0.5"
        assert config.port == 9999
        assert config.theme == "textual-nord"

    def test_cli_overrides_toml(self, tmp_path: Path):
        """CLI args override both defaults and config.toml."""
        cfg_dir = self._make_cfg_dir(
            tmp_path, '[server]\ndefault_ip = "10.0.0.5"\n'
        )
        from lm_tuio.config.settings import AppConfig

        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=cfg_dir / "config.toml",
        ):
            config, status = AppConfig.load(cli_args={"target": "192.168.0.1", "port": 443})

        assert config is not None
        assert config.target == "192.168.0.1"
        assert config.port == 443

    def test_load_invalid_port_falls_back(self, tmp_path: Path):
        """Invalid port in config.toml falls back to 1234."""
        cfg_dir = self._make_cfg_dir(
            tmp_path, '[server]\ndefault_port = 99999\n'
        )
        from lm_tuio.config.settings import AppConfig

        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=cfg_dir / "config.toml",
        ):
            config, status = AppConfig.load()

        assert config is not None
        assert config.port == 1234  # fallback
        assert "Invalid port number" in status

    def test_load_invalid_ip_adds_error(self, tmp_path: Path):
        """Invalid IP in config.toml adds error to logs."""
        cfg_dir = self._make_cfg_dir(
            tmp_path, '[server]\ndefault_ip = "999.0.0.1"\n'
        )
        from lm_tuio.config.settings import AppConfig

        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=cfg_dir / "config.toml",
        ):
            config, status = AppConfig.load()

        assert config is not None
        assert "Invalid IP or network format" in status

    def test_load_with_custom_path(self, tmp_path: Path):
        """custom_path bypasses get_config_path."""
        cfg = tmp_path / "custom.toml"
        cfg.write_text('[server]\ndefault_ip = "10.10.10.10"\n')
        from lm_tuio.config.settings import AppConfig

        config, status = AppConfig.load(custom_path=str(cfg))
        assert config is not None
        assert config.target == "10.10.10.10"

    def test_load_with_none_cli_args(self, tmp_path: Path):
        """cli_args=None skips CLI override."""
        cfg_dir = self._make_cfg_dir(tmp_path, '[server]\ndefault_ip = "10.0.0.1"\n')
        from lm_tuio.config.settings import AppConfig

        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=cfg_dir / "config.toml",
        ):
            config, status = AppConfig.load(cli_args=None)

        assert config is not None
        assert config.target == "10.0.0.1"


# ===== AppConfig.save =====


class TestAppConfigSave:
    """Test AppConfig.save and _build_toml_config."""

    def test_save_creates_new_file(self, tmp_path: Path):
        """Saving to a non-existent config file creates it."""
        cfg_dir = tmp_path / ".config" / "lm-tuio"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "config.toml"

        from lm_tuio.config.settings import AppConfig

        ac = AppConfig(config_path=str(cfg_dir))
        result = ac.save()

        assert cfg_file.exists()
        assert "Saved config" in result

    def test_save_writes_all_fields(self, tmp_path: Path):
        """All dataclass fields are written to TOML."""
        cfg_dir = tmp_path / ".config" / "lm-tuio"
        cfg_dir.mkdir(parents=True, exist_ok=True)

        from lm_tuio.config.settings import AppConfig

        ac = AppConfig(config_path=str(cfg_dir))
        ac.save()

        content = (cfg_dir / "config.toml").read_text()
        assert "default_ip" in content
        assert "default_port" in content
        assert "theme" in content
        assert "notify_timeout" in content
        assert "timezone" in content

    def test_save_preserves_existing_structure(self, tmp_path: Path):
        """Existing config.toml is updated, not replaced."""
        cfg_dir = tmp_path / ".config" / "lm-tuio"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_file = cfg_dir / "config.toml"

        # Write a custom section
        cfg_file.write_text("[custom]\nmy_key = \"hello\"\n")

        from lm_tuio.config.settings import AppConfig

        ac = AppConfig(config_path=str(cfg_dir))
        ac.save()

        content = cfg_file.read_text()
        assert "my_key" in content  # preserved
        assert "default_ip" in content  # added

    def test_save_handles_missing_parent_dir(self, tmp_path: Path):
        """Parent directories are created before writing."""
        deep = tmp_path / "a" / "b" / "c"
        from lm_tuio.config.settings import AppConfig

        ac = AppConfig(config_path=str(deep))
        result = ac.save()

        assert (deep / "config.toml").exists()
        assert "Saved config" in result

    def test_save_returns_error_on_failure(self, tmp_path: Path):
        """If write fails (e.g. read-only), returns error string."""
        from lm_tuio.config.settings import AppConfig

        deep = tmp_path / "deep" / "path" / "config.toml"
        ac = AppConfig(config_path=str(deep))
        result = ac.save()

        # Should return an error string, not raise
        assert isinstance(result, str)
        assert "Failed to save config" in result or "Saved config" in result


# ===== AppConfig._build_toml_config =====


class TestBuildTomlConfig:
    """Test _build_toml_config builds correct TOML structure."""

    def test_builds_correct_structure(self):
        """_build_toml_config produces correct TOML keys."""
        from lm_tuio.config.settings import AppConfig
        import tomlkit

        ac = AppConfig()
        doc = tomlkit.document()
        ac._build_toml_config(doc)

        assert "server" in doc
        assert "network" in doc
        assert "app" in doc
        assert doc["server"]["default_ip"] == "127.0.0.1"
        assert doc["server"]["default_port"] == 1234
        assert doc["app"]["theme"] == "textual-dark"
        assert doc["app"]["timezone"] == "America/New_York"

    def test_builds_empty_list_field(self):
        """cached_ips defaults to empty list."""
        from lm_tuio.config.settings import AppConfig
        import tomlkit

        ac = AppConfig()
        doc = tomlkit.document()
        ac._build_toml_config(doc)

        assert doc["server"]["cached_ips"] == []


# ===== validate_ip_net edge cases =====


class TestValidateIpNetEdgeCases:
    """Additional edge cases for validate_ip_net not covered in test_config.py."""

    def test_valid_subnet_24(self):
        """Valid /24 subnet normalizes correctly."""
        from lm_tuio.config.settings import validate_ip_net

        result, err = validate_ip_net("192.168.1.0/24")
        assert err is None
        assert result == "192.168.1.0/24"

    def test_valid_subnet_8(self):
        """Valid /8 subnet."""
        from lm_tuio.config.settings import validate_ip_net

        result, err = validate_ip_net("10.0.0.0/8")
        assert err is None
        assert result == "10.0.0.0/8"

    def test_invalid_ip_all_octets_max(self):
        """All octets at 255 is valid."""
        from lm_tuio.config.settings import validate_ip_net

        result, err = validate_ip_net("255.255.255.255")
        assert err is None
        assert result == "255.255.255.255/32"

    def test_invalid_ip_with_trailing_dot(self):
        """IP with trailing dot is invalid."""
        from lm_tuio.config.settings import validate_ip_net

        result, err = validate_ip_net("192.168.1.")
        assert err is not None
        assert result is None

    def test_invalid_ip_with_leading_zeros(self):
        """IP with leading zeros is invalid."""
        from lm_tuio.config.settings import validate_ip_net

        result, err = validate_ip_net("010.000.000.001")
        assert err is not None
        assert result is None

    def test_invalid_host_bits_on_subnet(self):
        """Host bits are allowed with strict=False."""
        from lm_tuio.config.settings import validate_ip_net

        result, err = validate_ip_net("192.168.1.0/24")
        assert err is None
        assert result == "192.168.1.0/24"

    def test_empty_string(self):
        """Empty string is invalid."""
        from lm_tuio.config.settings import validate_ip_net

        result, err = validate_ip_net("")
        assert err is not None
        assert result is None

    def test_hostname_not_ip(self):
        """Hostname is not a valid IP."""
        from lm_tuio.config.settings import validate_ip_net

        result, err = validate_ip_net("localhost")
        assert err is not None
        assert result is None
