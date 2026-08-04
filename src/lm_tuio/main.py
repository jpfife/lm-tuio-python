"""Entry point for LM TUIO application.

Spawns TUI if script flags not passed.
"""
# TODO: Add TUI vs Script detection and launch options

from textual.app import App

from lm_tuio.config.settings import AppConfig
from lm_tuio.screens.dashboard import DashboardScreen


class LMTuioApp(App):
    CSS_PATH = "styles.tcss"
    config: AppConfig

    def on_mount(self) -> None:
        loaded_config, err = AppConfig.load()
        self.config = loaded_config if loaded_config else AppConfig()

        if err:
            self.notify(
                f"Warning: Error occurred while loading configuration: {err}",
                severity="warning",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )

        dashboard: DashboardScreen = DashboardScreen()
        self.push_screen(dashboard)


def main():
    app = LMTuioApp()
    app.run()


if __name__ == "__main__":
    main()
