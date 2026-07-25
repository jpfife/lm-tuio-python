import sys
import asyncio
from lm_tui.config import parse_arguments, AppConfig
from lm_tui.scanner import scan_targets


async def execute_scan(config: AppConfig) -> None:
    print(f"Scanning target {config.target} on port {config.port}...")
    active_hosts: list[str] | None
    err: str | None

    active_hosts, err = await scan_targets(config)
    if err is not None:
        print(f"Error: {err}")
        sys.exit(3)

    assert isinstance(active_hosts, list)
    print()
    print("Scan complete. Found active endpoints on:")
    for host in active_hosts:
        print(f" -> {host}:{config.port}")


def main() -> None:
    config: AppConfig | None
    err: str | None

    config, err = parse_arguments()

    if err is not None:
        print(f"Error: {err}")
        sys.exit(1)

    assert isinstance(config, AppConfig)
    try:
        asyncio.run(execute_scan(config))
    except KeyboardInterrupt:
        print()
        print("Scan cancelled by user.")
        sys.exit(2)

if __name__ == '__main__':
    main()
