import sys
from lm_tui.config import parse_arguments, AppConfig


def main() -> None:
    config: AppConfig | None
    err: str | None

    config, err = parse_arguments()

    if err is not None:
        print(f"Error: {err}")
        sys.exit(1)

    assert isinstance(config, AppConfig)
    print(f"Target: {config.target}")
    print(f"Port: {config.port}")
    print(f"Network scan: {config.is_network}")


if __name__ == '__main__':
    main()
