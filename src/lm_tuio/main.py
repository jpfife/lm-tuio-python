from textual.app import App
from lm_tuio.screens.dashboard import DashboardScreen


class LMTuioApp(App):
    CSS_PATH = 'styles.tcss'

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())


def main():
    app = LMTuioApp()
    app.run()


if __name__ == '__main__':
    main()
