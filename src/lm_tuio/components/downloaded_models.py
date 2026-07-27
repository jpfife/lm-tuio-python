"""ListView widget for dashboard displaying all models downloaded on server."""

from textual.widgets import ListView


class DownloadedModels(ListView):
    def on_mount(self) -> None:
        # TODO: Figure out how ListViews work
        # TODO: Connect to ../api.py for api_actions['dl_models']
        pass
