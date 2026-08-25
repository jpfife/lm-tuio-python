"""Entry point for LM TUIO application.

Spawns TUI unless --help is passed via CLI.
"""

from textual.app import App

from lm_tuio.config import AppConfig, parse_cli
from lm_tuio.events import ActionLogUpdate
from lm_tuio.screens import DashboardScreen


class LMTuioApp(App):
    CSS_PATH = "styles.tcss"
    config: AppConfig

    def __init__(self, cli_args: dict[str, str | int] | None = None) -> None:
        super().__init__()
        self._cli_args = cli_args
        self._cli_api_key: str | None = None
        self._cli_config_path: str | None = None

        if not cli_args:
            return

        # Pop API key so it doesn't get written to the config on save/load
        if cli_args.get("api_key", None):
            key = cli_args.pop("api_key", None) or None
            if isinstance(key, str):
                self._cli_api_key = key

        if cli_args.get("config_path", None):
            path = cli_args.pop("config_path", None) or None
            if isinstance(path, str):
                self._cli_config_path = path

    def on_mount(self) -> None:
        loaded_config, err = AppConfig.load(
            cli_args=self._cli_args, custom_path=self._cli_config_path
        )
        self.config = loaded_config if loaded_config else AppConfig()

        if err:
            logs, ntfy = err, "warn"
        else:
            self.theme = self.config.theme
            self.timezone = self.config.timezone
            logs, ntfy = "Configuration loaded successfully", "ok"

        dashboard: DashboardScreen = DashboardScreen()
        self.push_screen(dashboard)

        # Delay push logs to ActionLog with message for py<3.14 backwards compatibility safe mount
        dashboard.post_message(ActionLogUpdate(logs, ntfy))


def main():
    cli_args = parse_cli()
    app = LMTuioApp(cli_args)
    app.run()


if __name__ == "__main__":
    main()
