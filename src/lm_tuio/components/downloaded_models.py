"""DataTable widget for dashboard displaying all models downloaded on server."""

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from lm_tuio.events import ModelSelected
from lm_tuio.models import ModelInfo


def format_bytes(size: int) -> str:
    """Converts bytes to MB or GB for model listing"""
    GB: int = 1024**3
    MB: int = 1024**2

    if size >= 1024**3:
        return f"{size} / {GB}"
    return f"{size} / {MB}"


class DownloadedModels(Static):
    """Widget to display all available models from the API endpoint"""

    def __init__(self):
        self._all_models: dict[str, ModelInfo] = {}
        self.dl_models_table: DataTable = DataTable(
            cursor_type="row", id="#dl-models-table"
        )

    def compose(self) -> ComposeResult:
        yield self.dl_models_table

    def on_mount(self) -> None:
        self.dl_models_table.add_columns("Name", "Size")

    def load_models(self, models: list[ModelInfo]) -> None:
        """Populate downloaded models dataset"""
        self._all_models = {m.key: m for m in models}
        # self.apply_filter("")

    def apply_filter(self, search_str: str) -> None:
        """Filter table on search_str"""
        self.dl_models_table.clear()
        term: str = search_str.lower()
        for model in self._all_models.values():
            if model.quantization is not None:
                if term in (
                    model.display_name.lower()
                    or model.publisher.lower()
                    or model.quantization.name.lower()
                ):
                    self.dl_models_table.add_row(
                        model.display_name,
                        format_bytes(model.size_bytes),
                        key=model.key,
                    )
            else:
                if term in (model.display_name.lower() or model.publisher.lower()):
                    self.dl_models_table.add_row(
                        model.display_name,
                        format_bytes(model.size_bytes),
                        key=model.key,
                    )

    def on_dl_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Pass model key for Context Pane model details display"""
        key = event.row_key.value
        assert key is not None

        model = self._all_models.get(key)
        self.post_message(ModelSelected(model))
