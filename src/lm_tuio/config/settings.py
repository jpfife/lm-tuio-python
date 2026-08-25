"""Configuration parser for managing app data and state.

Uses hierarchical loading strategy for parsing Defaults -> config.toml -> CLI args.
Config file pulling from working directory if present, otherwise XDG_CONFIG_HOME.
"""

import argparse
from dataclasses import MISSING, dataclass, field, fields
import ipaddress
from pathlib import Path
import tomllib
from typing import Any

import tomlkit

from lm_tuio.config import paths


SETTINGS_CONFIG: str = "config.toml"


@dataclass
class AppConfig:
    """Master app configuration dataclass."""

    # Table map for config.toml
    # SERVER
    target: str = field(
        default="127.0.0.1", metadata={"table": "server", "key": "default_ip"}
    )
    port: int = field(default=1234, metadata={"table": "server", "key": "default_port"})
    cached_ips: list[str] = field(
        default_factory=list, metadata={"table": "server", "key": "cached_ips"}
    )

    # NETWORK
    scan_subnet: str = field(
        default="192.168.1.0/24",
        metadata={"table": "network", "key": "default_scan_subnet"},
    )

    # APP
    NOTIFY_TIMEOUT: float = field(
        default=4.0, metadata={"table": "app", "key": "notify_timeout"}
    )
    MAX_CACHED_IPS: int = field(
        default=10, metadata={"table": "app", "key": "max_cached_ips"}
    )
    config_path: str = field(
        default="~/.config/lm-tuio",
        metadata={"table": "app", "key": "config_path"},
    )
    theme: str = field(
        default="textual-dark",
        metadata={"table": "app", "key": "theme"},
    )
    timezone: str = field(
        default="America/New_York",
        metadata={"table": "app", "key": "timezone"},
    )

    # Internal vars, no TOML map
    is_network: bool = False

    def _resolve_config_file(self) -> Path:
        """Resolve config file path from self.config_path.
        Handles file paths directly and appends config.toml to directories.
        """

        path: Path = Path(self.config_path)
        if path.is_file():
            return path

        path.mkdir(parents=True, exist_ok=True)
        return path / SETTINGS_CONFIG

    # NOTE: Using tomlkit to preserve structure, don't use tomllib functions for saving
    def save(self) -> str:
        """Save current state data to config_path, returns response string."""

        config_path: Path = self._resolve_config_file()

        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as file:
                    doc = tomlkit.parse(file.read())
            else:
                doc = tomlkit.document()

            self._build_toml_config(doc)

            with open(config_path, "w", encoding="utf-8") as file:
                file.write(tomlkit.dumps(doc))
            return f"Saved config to {config_path}"

        except Exception as err:
            return f"Failed to save config: {err}"

    @classmethod
    def load(
        cls,
        cli_args: dict[str, str | int] | None = None,
        custom_path: str | None = None,
    ) -> tuple["AppConfig | None", str | None]:
        """Load configs into AppConfig instance.
        Args:
            cli_args: pre-parsed CLI args dict from config parse_cli().
                Overrides defaults and config.toml. Pass None to skip.
            custom_path: Optional path to config.toml override.
        """

        conf_path: Path = (
            Path(custom_path) if custom_path else paths.get_config_path(SETTINGS_CONFIG)
        )

        # Defaults
        config_data: dict[str, Any] = {}
        for fld in fields(cls):
            if fld.default is not MISSING:
                config_data[fld.name] = fld.default
            elif fld.default_factory is not MISSING:
                config_data[fld.name] = fld.default_factory()

        logs: list[str] = []

        # Override defaults with config.toml
        missing_config: bool
        if conf_path.exists():
            missing_config = False
            toml_updates, toml_err = cls._parse_toml(conf_path)
            config_data.update(toml_updates)
            if toml_err:
                logs.append(toml_err)
        else:
            missing_config = True
            logs.append("config.toml not found.")

        # CLI args override defaults and config.toml
        # Parser handles err independently, only returns dict
        if cli_args:
            config_data.update(cli_args)

        valid_target, target_err = validate_ip_net(config_data["target"])
        valid_network, net_err = validate_ip_net(config_data["scan_subnet"])
        port_err, _ = validate_port(config_data["port"])

        # Check for fatal validation errors
        if target_err is not None:
            logs.append(target_err)
        else:
            assert isinstance(valid_target, str)
            config_data["is_network"] = "/32" not in valid_target

        if net_err is not None:
            logs.append(net_err)
        else:
            assert isinstance(valid_network, str)
            config_data["scan_subnet"] = valid_network

        if port_err is not None:
            logs.append(port_err)
            config_data["port"] = 1234

        config_data["config_path"] = str(conf_path)

        # NOTE: Add class attributes separate from dataclass fields
        config = cls(**config_data)  # Write config out if file was missing

        if missing_config:
            logs.append(cls.save(config))

        status_msg = "\n".join(logs) if logs else None

        return config, status_msg

    def _build_toml_config(self, doc: tomlkit.TOMLDocument) -> None:
        """Dynamically build TOML structure based on dataclass metadata."""

        logs: list[str] = []

        # Map fields from dataclass
        for fld in fields(self):
            table_name = fld.metadata.get("table")
            try:
                assert isinstance(table_name, str)
                if table_name not in doc:
                    doc.add(table_name, tomlkit.table())
            except AssertionError as err:
                logs.append(f"{err}")

        # Map dataclass to TOML config doc
        for fld in fields(self):
            table_name = fld.metadata.get("table")
            key_name = fld.metadata.get("key")

            if table_name and key_name:
                doc[table_name][key_name] = getattr(self, fld.name)

    @staticmethod
    def _parse_toml(conf_path: Path) -> tuple[dict[str, Any], str | None]:
        """Read TOML data and return a dictionary of valid updates."""

        updates: dict[str, Any] = {}
        try:
            with open(conf_path, "rb") as file:
                toml_data: dict[str, Any] = tomllib.load(file)

                for fld in fields(AppConfig):
                    table_name = fld.metadata.get("table")
                    key_name = fld.metadata.get("key")

                    if table_name is None or key_name is None:
                        continue
                    table_data = toml_data.get(table_name, {})
                    if key_name in table_data:
                        updates[fld.name] = table_data[key_name]
            return updates, None

        except Exception as err:
            return updates, f"Error reading config.toml: {err}"


def validate_port(port: int | str) -> tuple[str | None, str | None]:
    """Validate passed server port number.
    Arg type is validated by CLI parser on load, so ValueError should occur.
    """

    try:
        if isinstance(port, str):
            port_num: int = int(port)
        else:
            port_num: int = port
        assert 1 <= port_num <= 65535
    except ValueError:
        msg: str = "Scan port must be a number between 1-65535"
        severity = "error"
        return msg, severity
    except AssertionError:
        msg: str = "Invalid port number. Must be between 1-65535"
        severity = "error"
        return msg, severity
    return None, None


def validate_ip_net(target: str) -> tuple[str | None, str | None]:
    """Validate passed IP or subnet.

    Returns (valid_target_string, err)
        Success: err = None
        Fail: valid_target_string = None

    IPv4Network strict=False allows for host bits to be set for subnet scan.
    """

    try:
        network_obj: ipaddress.IPv4Network = ipaddress.IPv4Network(target, strict=False)
        return str(network_obj), None
    except ValueError:
        pass  # Check if single IP

    try:
        ip_obj: ipaddress.IPv4Address = ipaddress.IPv4Address(target)
        return str(ip_obj), None
    except ValueError:
        return (
            None,
            f"Invalid IP or network format: '{target}'\nSee --help for usage information.",
        )
