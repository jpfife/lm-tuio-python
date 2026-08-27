"""CLI argument parsing for lm-tuio.

Return parsed args as dict for downstream use by AppConfig."""

import argparse
from functools import partial

from rich_argparse import RawTextRichHelpFormatter


# Map arg names to AppConfig field names and types
CLI_OVERRIDE_MAP: dict[str, tuple[list[str], type]] = {
    "target": (["target"], str),
    "network": (["scan_subnet"], str),
    "port": (["port"], int),
    "api_key": (["api_key"], str),
    "config_file": (["config_path"], str),
    "theme": (["theme"], str),
    "timezone": (["timezone"], str),
}

WideFormatter = partial(RawTextRichHelpFormatter, max_help_position=40, width=120)

desc: str = (
    "LM Studio remote server management and TUI interface.\n\n"
    "Connect on launch to API endpoint:\n  lm-tuio -t 192.168.1.10 -p 10100 # (optional) -k 'my-api-key'\n"
)

epilog: str = "Jordan Fife <jpfife@redappr.com>"

cust_usage: str = (
    "%(prog)s\t[-h|--help]\n "
    "\t\t[-c|--config-file FILE|PATH] [-n|--network SUBNET] \n"
    "\t\t[-t|--target IP -p|--port NUM [-k|--api-key KEY]]"
)


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
        prog="lm-tuio",
        # usage=cust_usage,
        description=desc,
        epilog=epilog,
        formatter_class=WideFormatter,
    )

    # Args list
    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        metavar="FILE|PATH",
        help="Use specified configuration file, or create config directory by specifying path",
    )
    parser.add_argument(
        "-k",
        "--api-key",
        type=str,
        metavar="KEY",
        action=RequiresTargetAndPort,
        help="API key for target server (requires --target and --port)",
    )
    parser.add_argument(
        "-n",
        "--network",
        type=str,
        metavar="SUBNET",
        help="Set scan network subnet with CIDR notation (Ex: 192.168.2.0/24)",
    )
    parser.add_argument(
        "-p", "--port", type=int, metavar="PORT", help="Set server port"
    )
    parser.add_argument(
        "-t", "--target", type=str, metavar="IP", help="Set target server IP address"
    )
    parser.add_argument(
        "-T",
        "--theme",
        type=str,
        metavar="THEME",
        help="Set application theme (e.g. textual-dark, gruvbox, dracula, etc.)",
    )
    parser.add_argument(
        "-Z",
        "--timezone",
        type=str,
        metavar="TZ",
        help="Set timezone for log timestamps (e.g. America/Los_Angeles)",
    )

    raw: dict[str, str | int] = vars(parser.parse_args())
    updates: dict[str, str | int] = {}

    for arg_name, (targets, typ) in CLI_OVERRIDE_MAP.items():
        val = raw.get(arg_name)
        if val is None:
            continue
        for target in targets:
            updates[target] = typ(val) if typ is not str else val

    return updates
