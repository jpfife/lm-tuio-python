"""Entry point for LM TUIO application.

Spawns TUI if flags for script use are not present.
"""
# TODO: Add TUI vs Script detection and launch options

from textual.app import App

from lm_tuio.screens.dashboard import DashboardScreen


class LMTuioApp(App):
    CSS_PATH = "styles.tcss"

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())


def main():
    app = LMTuioApp()
    app.run()


if __name__ == "__main__":
    main()
