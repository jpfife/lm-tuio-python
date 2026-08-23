"""Tests for ../src/lm_tuio/config/settings.py.

Tests parsing and validation functionality for CLI args.
"""

import sys

from lm_tuio.config import parse_cli, validate_ip_net


# NOTE: validate_ip_net() uses the ipaddress module which automatically
#       appends CIDR subnet notation to a valid, single IPv4 address ('/32').


def test_validate_ip_net_single_ip() -> None:
    target: str = "100.10.5.1"
    valid_target: str | None
    err: str | None
    valid_target, err = validate_ip_net(target)

    assert err is None
    assert valid_target == "100.10.5.1/32"


def test_validate_ip_net_single_ip_invalid_format() -> None:
    target: str = "10.11.12."
    valid_target: str | None
    err: str | None
    valid_target, err = validate_ip_net(target)

    assert err is not None
    assert valid_target is None


def test_validate_ip_net_with_subnet() -> None:
    target: str = "100.10.5.1/16"
    valid_target: str | None
    err: str | None
    valid_target, err = validate_ip_net(target)

    assert err is None
    assert valid_target == "100.10.0.0/16"


# TEST: PARSER VALIDATION using lm_tuio.cli.parse_cli()

# parse_cli() reads sys.argv directly, so we mock sys.argv for each test.


def test_parse_cli_defaults(monkeypatch) -> None:
    """No args passed; return empty dict."""

    monkeypatch.setattr(sys, "argv", ["lm-tuio"])
    updates = parse_cli()

    assert updates == {}


def test_parse_cli_multi_target_flags(monkeypatch) -> None:
    """Single IP passed via --target."""

    monkeypatch.setattr(
        sys, "argv", ["lm-tuio", "-t", "100.64.0.10", "-t", "100.64.0.5"]
    )
    updates = parse_cli()

    assert updates == {"target": "100.64.0.5"}


def test_parse_cli_flags(monkeypatch) -> None:
    """Pass all server/network flags through to config."""

    monkeypatch.setattr(
        sys, "argv", ["lm-tuio", "-t", "100.24.8.28", "-n", "10.0.0.0/8", "-p", "8080"]
    )
    updates = parse_cli()

    assert updates is not None
    assert updates["target"] == "100.24.8.28"
    assert updates["scan_subnet"] == "10.0.0.0/8"
    assert updates["port"] == 8080


def test_parse_cli_invalid_ip(monkeypatch) -> None:
    """Invalid inputs are still captured (validation happens in load())."""

    monkeypatch.setattr(sys, "argv", ["lm-tuio", "-t", "999.999.999.999"])
    updates = parse_cli()

    assert updates is not None
    assert updates["target"] == "999.999.999.999"


def test_parse_cli_invalid_port(monkeypatch) -> None:
    """Invalid inputs are still captured (validation happens in load())."""

    monkeypatch.setattr(sys, "argv", ["lm-tuio", "-p", "1234567"])
    updates = parse_cli()

    assert updates is not None
    assert updates["port"] == 1234567


def test_parse_cli_invalid_network(monkeypatch) -> None:
    """Invalid inputs are still captured (validation happens in load())."""

    monkeypatch.setattr(sys, "argv", ["lm-tuio", "-n", "192.168.1.1"])
    updates = parse_cli()

    assert updates is not None
    assert updates["scan_subnet"] == "192.168.1.1"
