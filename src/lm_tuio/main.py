"""Entry point for LM TUIO application.

Spawns TUI if script flags not passed.
"""
# TODO: Add TUI vs Script detection and launch options

import sys

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

    def on_mount(self) -> None:
        loaded_config, err = AppConfig.load(cli_args=self._cli_args)
        self.config = loaded_config if loaded_config else AppConfig()

        if err:
            logs, ntfy = err, "warn"
        else:
            logs, ntfy = "Configuration loaded successfully", "ok"

        dashboard: DashboardScreen = DashboardScreen()
        self.push_screen(dashboard)

        # Push logs to ActionLog
        dashboard.update_action_log(event=ActionLogUpdate(logs, ntfy))


def main():
    cli_args = parse_cli()
    app = LMTuioApp(cli_args)
    app.run()


if __name__ == "__main__":
    main()
