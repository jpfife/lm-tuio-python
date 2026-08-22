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

    # Internal vars, no TOML map
    is_network: bool = False

    # NOTE: Using tomlkit to preserve structure, don't use tomllib functions for saving
    def save(self) -> str:
        """Save current state data to config_path, returns response string."""

        config_path: Path = paths.get_config_path(SETTINGS_CONFIG)

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
        cls, args_list: list[str] | None = None, custom_path: str | None = None
    ) -> tuple["AppConfig | None", str | None]:
        """Load configs into AppConfig instance."""

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
        if args_list:
            assert isinstance(args_list, list)
            cli_updates = cls._parse_arguments(args_list)
            config_data.update(cli_updates)

        valid_target, err = validate_ip_net(config_data["target"])
        valid_network, net_err = validate_ip_net(config_data["scan_subnet"])

        # Check for fatal validation error
        if err is not None:
            return None, err
        if net_err is not None:
            return None, net_err

        assert isinstance(valid_target, str)
        assert isinstance(valid_network, str)
        config_data["is_network"] = "/32" not in valid_target
        config_data["scan_subnet"] = valid_network
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

    @staticmethod
    def _parse_arguments(args_list: list[str]) -> dict[str, Any]:
        """Parse CLI args and return a dictionary of valid updates."""

        parser = argparse.ArgumentParser(
            description="LM Studio remote server management and TUI interface."
        )
        parser.add_argument(
            "target_ip", nargs="?", type=str, help="Target IP address or subnet"
        )
        parser.add_argument("-n", "--network", type=str, help="Target network subnet")
        parser.add_argument("-p", "--port", type=int, help="Target port")

        parsed_args = vars(parser.parse_args(args_list))
        updates: dict[str, Any] = {}

        # Apply CLI overrides
        if parsed_args.get("target_ip"):
            updates["target"] = str(parsed_args["target_ip"])
        if parsed_args.get("port"):
            updates["port"] = int(parsed_args["port"])
        if parsed_args.get("network"):
            updates["scan_subnet"] = str(parsed_args["network"])

        return updates


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
