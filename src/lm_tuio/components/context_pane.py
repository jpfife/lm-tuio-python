"""Dynamic widget to display relevant information for dashboard focus item."""

from textual.widgets import DataTable


class ContextPane(DataTable):
    def on_mount(self) -> None:
        # TODO: Build out table formats for model info display and network stats.
        pass
