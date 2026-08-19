"""Entry point for LM TUIO application.

Spawns TUI if script flags not passed.
"""
# TODO: Add TUI vs Script detection and launch options

from textual.app import App

from lm_tuio.config.settings import AppConfig
from lm_tuio.events import ActionLogUpdate
from lm_tuio.screens.dashboard import DashboardScreen


class LMTuioApp(App):
    CSS_PATH = "styles.tcss"
    config: AppConfig

    def on_mount(self) -> None:
        loaded_config, err = AppConfig.load()
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
    app = LMTuioApp()
    app.run()


if __name__ == "__main__":
    main()
