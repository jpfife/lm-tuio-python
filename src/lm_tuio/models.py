"""Establishes data structures for LMS Native v1 REST API GET Models response.

Optional JSON fields from API response may be 'None'.
"""

from enum import StrEnum

from pydantic import BaseModel
from textual import on
from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from lm_tuio.events import ModelSelected


def format_bytes(size: int) -> str:
    """Converts bytes to MB or GB for model listing"""
    TB: int = 1024**4
    GB: int = 1024**3
    MB: int = 1024**2

    if size >= TB:
        return f"{size / TB:.2f} GB"
    elif size >= GB:
        return f"{size / GB:.2f} GB"
    return f"{size / MB:.2f} MB"


class QuantizationInfo(BaseModel):
    """Model quantization information."""

    name: str
    bits_per_weight: int | float | None = None


class ModelInfo(BaseModel):
    """Single model block returned by LM Studio Native v1 REST API."""

    type: str
    publisher: str
    key: str  # Unique ID for API calls
    display_name: str
    architecture: str | None = None
    size_bytes: int
    params_string: str | None = None
    max_context_length: int
    format: str
    quantization: QuantizationInfo | None = None


class ModelListResponse(BaseModel):
    """Top-level JSON response from /api/v1/models endpoint."""

    models: list[ModelInfo]


class BaseModelTable(Static):
    """Base class for model display tables (Loaded/Downloaded models)"""

    BINDINGS = [
        ("n", "sort_on_name", "[sort name]"),
        ("s", "sort_on_size", "[sort size]"),
    ]

    class SortType(StrEnum):
        NAME = "name"
        SIZE = "size"

    def __init__(self, table_id: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.table_id = table_id
        self.table: DataTable = DataTable(cursor_type="row", id=self.table_id)
        self._all_models: dict[str, ModelInfo] = {}
        self.current_filter: str = ""
        self.current_sort: str = "name"
        self.sort_reverse: bool = False

    def compose(self) -> ComposeResult:
        yield self.table

    def on_mount(self) -> None:
        self.table.add_columns("Name", "Size")

    def load_models(self, models: list[ModelInfo]) -> None:
        """Populate downloaded models dataset"""
        # self.clear_model_list()
        self._all_models = {m.key: m for m in models}
        # self.apply_filter("")
        self.refresh_table()

    def apply_filter(self, search_term: str) -> None:
        """Updates filter criteria and refreshes display"""
        self.current_filter = search_term.lower()
        self.refresh_table()

    def refresh_table(self) -> None:
        """Filter, sort, and model table"""
        self.table.clear()

        filtered_models = [
            m
            for m in self._all_models.values()
            if self.current_filter in m.display_name.lower()
            or self.current_filter in m.publisher.lower()
        ]

        if self.current_sort == self.SortType.NAME:
            filtered_models.sort(
                key=lambda m: m.display_name.lower(), reverse=self.sort_reverse
            )
        elif self.current_sort == self.SortType.SIZE:
            filtered_models.sort(key=lambda m: m.size_bytes, reverse=self.sort_reverse)

        for model in filtered_models:
            self.table.add_row(
                model.display_name,
                format_bytes(model.size_bytes),
                key=model.key,
            )

        if self.table.row_count > 0:
            self.table.move_cursor(row=0)
        else:
            self.post_message(ModelSelected(None))

    def action_sort_on_name(self) -> None:
        """Sort model table by display name, or reverse sort if already sorted on name."""
        if self.current_sort == self.SortType.NAME:
            self.sort_reverse = not self.sort_reverse
        else:
            self.current_sort = self.SortType.NAME
            self.sort_reverse = False
        self.refresh_table()

    def action_sort_on_size(self) -> None:
        """Sort model table by size of model, or reverse sort if already sorted on size."""
        if self.current_sort == self.SortType.SIZE:
            self.sort_reverse = not self.sort_reverse
        else:
            self.current_sort = self.SortType.SIZE
            self.sort_reverse = True  # Default display largest models first
        self.refresh_table()

    @on(DataTable.RowHighlighted)
    def handle_row_highlight(self, event: DataTable.RowHighlighted) -> None:
        """Fires when navigating through table."""
        key = event.row_key.value
        assert key
        model = self._all_models.get(key)
        self.post_message(ModelSelected(model))


# Model DataTable implementations


class DownloadedModels(BaseModelTable):
    """Widget displaying all downloaded models available on the server."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(table_id="dl-models-table", *args, **kwargs)


class LoadedModels(BaseModelTable):
    """Widget displaying currently loaded models for immediate use."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(table_id="loaded-models-table", *args, **kwargs)
