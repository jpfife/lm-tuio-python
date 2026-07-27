"""Live log feed and action status widget for primary dashboard."""

from textual.widgets import Log


class ActionLog(Log):
    def on_mount(self) -> None:
        # TODO: Figure out how logs work
        pass
