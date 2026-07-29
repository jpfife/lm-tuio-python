"""Configuration parser for managing app data and state.

Uses hierarchical loading strategy for parsing Defaults -> config.toml -> CLI args.
Update _build_toml_config and _parse_toml helper methods when adding tables to config.toml !!
"""

import argparse
import ipaddress
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomlkit


@dataclass
class AppConfig:
    """Standardize network type requirements."""

    target: str = "127.0.0.1"  # IPv4 only
    port: int = 1234
    scan_subnet: str = "192.168.1.0/24"  # in CIDR notation
    is_network: bool = False
    NOTIFY_TIMEOUT: float = 2.0
    config_path: Path = Path("config.toml")

    # NOTE: Using tomlkit to preserve structure, don't use tomllib functions for saving
    def save(self) -> str:
        """Saves current state data to config_path, returns result string"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as file:
                    doc = tomlkit.parse(file.read())
            else:
                doc = tomlkit.document()

            self._build_toml_config(doc)

            with open(self.config_path, "w", encoding="utf-8") as file:
                file.write(tomlkit.dumps(doc))

            return f"Saved config to {self.config_path}"

        except Exception as err:
            return f"Failed to save config: {err}"

    @classmethod
    def load(
        cls, args_list: list[str] | None = None, custom_path: str | None = None
    ) -> tuple["AppConfig | None", str | None]:
        """Method for loading configs into AppConfig instance."""

        conf_path: Path = Path(custom_path) if custom_path else cls.config_path

        # Defaults
        config_data: dict[str, Any] = {
            "target": cls.target,
            "port": cls.port,
            "scan_subnet": cls.scan_subnet,
        }
        logs: list[str] = []

        # Override defaults with config.toml
        if conf_path.exists():
            toml_updates, toml_err = cls._parse_toml(conf_path)
            config_data.update(toml_updates)
            if toml_err:
                logs.append(toml_err)
        else:
            logs.append("Warning: config.toml not found.")

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
        is_network_scan = "/32" not in valid_target

        # Compile non-fatal logs
        status_msg = "\n".join(logs) if logs else None

        config = cls(
            target=config_data["target"],
            port=config_data["port"],
            scan_subnet=valid_network,
            is_network=is_network_scan,
            NOTIFY_TIMEOUT=config_data["notify_timeout"],
            config_path=conf_path,
        )

        return config, status_msg

    # NOTE: Update _build_toml_config helper method when adding tables to config.toml !!
    def _build_toml_config(self, doc: tomlkit.TOMLDocument) -> None:
        """Initializes config TOML tables and maps current state."""

        # Check for/add root config tables
        for table in ["server", "network", "app"]:
            if table not in doc:
                doc.add(table, tomlkit.table())

        # Map onto AppConfig dataclass
        doc["server"]["default_ip"] = self.target
        doc["server"]["default_port"] = self.port
        doc["network"]["default_scan_subnet"] = self.scan_subnet
        doc["app"]["notify_timeout"] = self.NOTIFY_TIMEOUT

    # NOTE: Update _parse_toml helper method when adding tables to config.toml !!
    @staticmethod
    def _parse_toml(conf_path: Path) -> tuple[dict[str, Any], str | None]:
        """Reads TOML and returns a dictionary of valid updates."""
        updates: dict[str, Any] = {}
        try:
            with open(conf_path, "rb") as file:
                toml_data: dict[str, Any] = tomllib.load(file)
                server_toml: dict[str, Any] = toml_data.get("server", {})
                network_toml: dict[str, Any] = toml_data.get("network", {})
                app_toml: dict[str, Any] = toml_data.get("app", {})

                if "default_ip" in server_toml:
                    updates["target"] = server_toml["default_ip"]
                if "default_port" in server_toml:
                    updates["port"] = server_toml["default_port"]
                if "default_scan_subnet" in network_toml:
                    updates["scan_subnet"] = network_toml["default_scan_subnet"]
                if "notify_timeout" in app_toml:
                    updates["notify_timeout"] = app_toml["notify_timeout"]

            return updates, None
        except Exception as err:
            return updates, f"Error reading config.toml: {err}"

    @staticmethod
    def _parse_arguments(args_list: list[str]) -> dict[str, Any]:
        """Parses CLI args and returns a dictionary of valid updates."""
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
    """
    Validates passed IP or subnet.
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
