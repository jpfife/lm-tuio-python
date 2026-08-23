"""CLI argument parsing for lm-tuio.

Return parsed args as dict for downstream use by AppConfig."""

import argparse

# Map arg names to AppConfig field names and types
CLI_OVERRIDE_MAP: dict[str, tuple[list[str], type]] = {
    "target": (["target"], str),
    "network": (["scan_subnet"], str),
    "port": (["port"], int),
    "api_key": (["api_key"], str),
    "config_file": (["config_path"], str),
}


class RequiresTargetAndPort(argparse.Action):
    """Validate that --target and --port are set when --api-key is used."""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        target = getattr(namespace, "target", None)
        port = getattr(namespace, "port", None)
        if target is None or port is None:
            parser.error(f"--{self.dest} requires --target and --port")


def parse_cli() -> dict[str, str | int] | None:
    """Parse CLI arguments.

    Returns:
        dict of parsed args, or None if --help was passed and exits.
    """

    parser = argparse.ArgumentParser(
        description="LM Studio remote server management and TUI interface."
    )

    # Args list
    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        help="Use specified configuration file, or create config directory by specifying path",
    )
    parser.add_argument(
        "-k",
        "--api-key",
        type=str,
        action=RequiresTargetAndPort,
        help="API key for target server (requires --target and --port)",
    )
    parser.add_argument(
        "-n",
        "--network",
        type=str,
        help="Set server network subnet with CIDR notation (Ex: 192.168.1.25/24)",
    )
    parser.add_argument("-p", "--port", type=int, help="Set server port")
    parser.add_argument("-t", "--target", type=str, help="Set target server IP address")

    raw: dict[str, str | int] = vars(parser.parse_args())
    updates: dict[str, str | int] = {}

    for arg_name, (targets, typ) in CLI_OVERRIDE_MAP.items():
        val = raw.get(arg_name)
        if val is None:
            continue
        for target in targets:
            updates[target] = typ(val) if typ is not str else val

    return updates
