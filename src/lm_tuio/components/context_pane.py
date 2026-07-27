from textual.widgets import DataTable


class ContextPane(DataTable):
    '''Dynamic widget to display relevant information for focus item on dashboard.'''
    def on_mount(self) -> None:
        # TODO: Build out table formats for model info display and network stats.
        pass
