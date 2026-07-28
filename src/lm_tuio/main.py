"""Entry point for LM TUIO application.

Spawns TUI if script flags not passed.
"""
# TODO: Add TUI vs Script detection and launch options

from textual.app import App

from lm_tuio.config import AppConfig
from lm_tuio.events import ServerEndpointUpdated
from lm_tuio.screens.dashboard import DashboardScreen


class LMTuioApp(App):
    CSS_PATH = "styles.tcss"

    def on_mount(self) -> None:
        config, err = AppConfig.load()
        if err:
            self.notify(err, severity="warning")

        dashboard: DashboardScreen = DashboardScreen()
        self.push_screen(dashboard)

        if config:
            dashboard.post_message(ServerEndpointUpdated(config.target, config.port))


def main():
    app = LMTuioApp()
    app.run()


if __name__ == "__main__":
    main()
