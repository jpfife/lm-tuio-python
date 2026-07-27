import argparse
from dataclasses import dataclass
import ipaddress


@dataclass
class AppConfig:
    """For autocomplete and type safety."""

    target: str
    port: int
    is_network: bool


def validate_ip_net(target: str) -> tuple[str | None, str | None]:
    """
    Validates passed IP or subnet.
    Returns (valid_target_string, err)
        Success: err = None
        Fail: valid_target_string = None

    IPv4Network strict=False allows for host bits to be set for subnet scan (192.168.1.5/24 is valid for subnet definition)
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


def parse_arguments(
    args_list: list[str] | None = None,
) -> tuple[AppConfig | None, str | None]:
    """Returns tuple: (AppConfig, err)"""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="LM Studio server detection and TUI interface."
    )

    # Positional args
    parser.add_argument(
        "target_ip", nargs="?", type=str, help="Target IP address or subnet"
    )
    parser.add_argument("target_port", nargs="?", type=int, help="Target port")
    # Flags
    parser.add_argument(
        "-n",
        "--network",
        type=str,
        help="Target network subnet (default = 192.168.1.0/24)",
    )
    parser.add_argument("-p", "--port", type=int, help="Target port")

    parsed_args: dict[str, str | int | None] = vars(parser.parse_args(args_list))

    # Determine scan parameters
    scan_target: str = "192.168.1.0/24"  # Default subnet scan
    if parsed_args.get("target_ip") is not None:
        assert isinstance(parsed_args["target_ip"], str)
        scan_target = parsed_args["target_ip"]
    elif parsed_args.get("network") is not None:
        assert isinstance(parsed_args["network"], str)
        scan_target = parsed_args["network"]

    scan_port: int = 1234
    if parsed_args.get("target_port") is not None:
        assert isinstance(parsed_args["target_port"], int)
        scan_port = parsed_args["target_port"]
    elif parsed_args.get("port") is not None:
        assert isinstance(parsed_args["port"], int)
        scan_port = parsed_args["port"]

    valid_target, err = validate_ip_net(scan_target)
    if isinstance(valid_target, str):
        is_network_scan: bool = "/32" not in valid_target
    else:
        return None, err

    if err is not None:
        return None, err

    config: AppConfig = AppConfig(valid_target, scan_port, is_network_scan)

    return config, None
