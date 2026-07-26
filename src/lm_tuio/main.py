import sys
import asyncio
from lm_tuio.config import parse_arguments, AppConfig
from lm_tuio.scanner import scan_targets
from lm_tuio.api import fetch_available_models
from lm_tuio.tui import LMStudioApp


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


# def main() -> None:
#     config: AppConfig | None
#     err: str | None
#
#     config, err = parse_arguments()
#
#     if err is not None:
#         print(f"Error: {err}")
#         sys.exit(1)
#
#     assert isinstance(config, AppConfig)
#     try:
#         asyncio.run(execute_scan(config))
#     except KeyboardInterrupt:
#         print()
#         print("Scan cancelled by user.")
#         sys.exit(2)

def main() -> None:
    config: AppConfig | None
    err: str | None

    config, err = parse_arguments(sys.argv[1:])
    if err or (config is None):
        print(f"Configuration error: {err}")
        sys.exit(1)

    ip: str = config.target.split('/')[0]
    port: int = config.port

    app = LMStudioApp(ip, port)
    app.run()

if __name__ == '__main__':
    main()
