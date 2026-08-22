"""Tests for ../src/lm_tuio/config/settings.py.

Tests parsing and validation functionality for CLI args.
"""

from lm_tuio.config.settings import AppConfig, validate_ip_net

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


# TEST: PARSER VALIDATION using config.AppConfig._parse_arguments():


def test_parse_arguments_defaults() -> None:
    """Use default subnet and port when positional args are absent."""
    config: AppConfig | None
    err: str | None
    config, err = AppConfig._parse_arguments([])

    assert err is None
    assert config is not None
    assert config.target == "192.168.1.0/24"
    assert config.port == 1234
    assert config.is_network is True


def test_parse_arguments_positional_ip() -> None:
    """Single IP passed to parser."""
    config: AppConfig | None
    err: str | None
    config, err = AppConfig._parse_arguments(["100.64.0.5"])

    assert err is None
    assert config is not None
    assert config.target == "100.64.0.5/32"
    assert config.is_network is False


def test_parse_arguments_flags() -> None:
    """Pass a custom network and port via CLI flags."""
    config: AppConfig | None
    err: str | None
    config, err = AppConfig._parse_arguments(["-n", "10.0.0.0/8", "-p", "8080"])

    assert err is None
    assert config is not None
    assert config.target == "10.0.0.0/8"
    assert config.port == 8080
    assert config.is_network is True


def test_parse_arguments_invalid_input() -> None:
    """Invalid inputs return the expected error tuple without crashing."""
    config: AppConfig | None
    err: str | None
    config, err = AppConfig._parse_arguments(["999.999.999.999"])

    assert config is None
    assert err is not None
    assert "Invalid IP or network format" in err
