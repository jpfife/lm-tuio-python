"""Configuration parser for managing app data and state.

Uses hierarchical loading strategy for parsing Defaults -> config.toml -> CLI args.
"""

import argparse
import ipaddress
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    """Standardize network type requirements."""

    target: str  # IPv4 only
    port: int
    scan_subnet: str  # in CIDR notation
    is_network: bool

    NOTIFY_TIMEOUT: float = 2.0

    @classmethod
    def load(
        cls, args_list: list[str] | None = None
    ) -> tuple["AppConfig | None", str | None]:
        """Factory method for config generation"""

        # Defaults
        config_data: dict[str, Any] = {
            "target": "127.0.0.1",
            "port": 1234,
            "scan_subnet": "192.168.1.0/24",
        }
        config_path: Path = Path("config.toml")
        logs: list[str] = []

        # Override defaults with config.toml
        if config_path.exists():
            toml_updates, toml_err = cls._parse_toml(config_path)
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

        # Check for fatal validation error
        if err is not None:
            return None, err

        assert isinstance(valid_target, str)
        is_network_scan = "/32" not in valid_target

        # Compile non-fatal logs
        status_msg = "\n".join(logs) if logs else None

        config = cls(
            target=valid_target,
            port=config_data["port"],
            scan_subnet=config_data["scan_subnet"],
            is_network=is_network_scan,
        )

        return config, status_msg

    @staticmethod
    def _parse_toml(conf_path: Path) -> tuple[dict[str, Any], str | None]:
        """Reads TOML and returns a dictionary of valid updates."""
        updates: dict[str, Any] = {}
        try:
            with open(conf_path, "rb") as f:
                toml_data: dict[str, Any] = tomllib.load(f)
                server_toml: dict[str, Any] = toml_data.get("server", {})
                network_toml: dict[str, Any] = toml_data.get("network", {})

                if "default_ip" in server_toml:
                    updates["target"] = server_toml["default_ip"]
                if "default_port" in server_toml:
                    updates["port"] = server_toml["default_port"]
                if "default_scan_subnet" in network_toml:
                    updates["scan_subnet"] = network_toml["default_scan_subnet"]

            return updates, None
        except Exception as e:
            return updates, f"Error reading config.toml: {e}"

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
