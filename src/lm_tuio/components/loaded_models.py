"""Display widget for LMS loaded models for dashboard."""

from textual.widgets import ListView


class LoadedModels(ListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        # TODO: Figure out how ListView widgets work
        # TODO: Connect with ../api.py for api_actions['models']
        pass
