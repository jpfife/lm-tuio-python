"""Live log feed and action status widget for primary dashboard."""

from textual.widgets import Log


class ActionLog(Log):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        # TODO: Figure out how logs work
        pass
