"""Establishes data structures for LMS Native v1 REST API GET Models response and display.

Optional JSON fields from API response may be 'None'.
"""

from _collections_abc import Callable
from enum import StrEnum

from pydantic import BaseModel
from textual import on
from textual.app import ComposeResult
from textual.events import DescendantBlur, DescendantFocus
from textual.widgets import DataTable, Static

from lm_tuio.config import keymap


def format_bytes(size: int) -> str:
    """Converts bytes to MB or GB for model listing"""
    TB: int = 1024**4
    GB: int = 1024**3
    MB: int = 1024**2
    KB: int = 1024

    if size >= TB:
        return f"{size / TB:.2f} TB"
    elif size >= GB:
        return f"{size / GB:.2f} GB"
    elif size >= MB:
        return f"{size / MB:.2f} MB"
    return f"{int(size / KB)}K"


def estimate_context_cache_memory(file_size_bytes: int, context_size_bytes) -> int:
    """Loose estimation of context memory cache cost based on typical GQA model setups.

    Estimated number of model layers based on base size of the model to determine
    base token cost, using 3-tier param size approach for typical local model setups
    at +/- 4-bit quants.
    Using 4K token:
    (8 KV Heads, 128 dimension, (K state + V state bytes),
    at full precision KV cache (2 bytes).
    KV cache cost per token:
    <8B, <7 GB ~ 32 layers = 131 KB / token
    <32B, <28 GB ~ 64 layers = 262 KB / token
    35-70B+, 28 GB+ ~ 80 layers = 328 KB / token
    """
    GB: int = 1024**3
    tier1_token: int = 32 * 4096
    tier2_token: int = 64 * 4096
    tier3_token: int = 80 * 4096
    bytes_per_token: int = 0

    file_GB: int = file_size_bytes // GB
    if file_GB < 7:
        bytes_per_token = tier1_token
    elif file_GB < 28:
        bytes_per_token = tier2_token
    else:
        bytes_per_token = tier3_token

    return context_size_bytes * bytes_per_token


# ======= DATA STRUCTS ========


class ModelConfig(BaseModel):
    """Specific loaded instance model configuration."""

    context_length: int
    eval_batch_size: int | None = None
    physical_batch_size: int | None = None
    parallel: int | None = None
    flash_attention: bool | None = None
    context_checkpoints: int | None = None
    reasoning_budget_message: str | None = None

    speculative_draft_mtp: bool | None = None
    speculative_draft_simple: bool | None = None
    speculative_draft_model: str | None = None
    speculative_draft_max_tokens: int | None = None
    speculative_draft_min_tokens: int | None = None
    speculative_draft_min_continue_probability: float | None = None

    num_experts: int | None = None
    offload_kv_cache_to_gpu: bool | None = None


class LoadedInstance(BaseModel):
    """Loaded instance and specific configuration information."""

    id: str
    config: ModelConfig


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
    loaded_instances: list[LoadedInstance]
    format: str
    quantization: QuantizationInfo | None = None


class ModelListResponse(BaseModel):
    """Top-level JSON response from /api/v1/models endpoint."""

    models: list[ModelInfo]


# ======= MODEL TABLE CLASSES =======


class BaseModelTable(Static):
    """Base class for model display tables (Loaded/Downloaded models)"""

    BINDINGS = keymap.KeymapManager.get_bindings("tables")

    class SortType(StrEnum):
        NAME = "name"
        SIZE = "size"

    def __init__(
        self,
        table_id: str,
        post_highlighted_model_callback: Callable[[ModelInfo | None]],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.table_id = table_id
        self.table: DataTable = DataTable(cursor_type="row", id=self.table_id)
        self._all_models: dict[str, ModelInfo] = {}
        self.current_filter: str = ""
        self.current_sort: str = "name"
        self.sort_reverse: bool = False

        # Post message callback for event bus
        self.post_highlighted_model = post_highlighted_model_callback

    def compose(self) -> ComposeResult:
        yield self.table

    def on_mount(self) -> None:
        self.table.add_columns("Name", "Size")

    def clear_model_list(self) -> None:
        self._all_models.clear()

    def load_models(self, models: list[ModelInfo]) -> None:
        """Populate downloaded models dataset"""
        self.clear_model_list()
        self._all_models = {m.key: m for m in models}
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
            or self.current_filter in m.key.lower()
            or (m.quantization and self.current_filter in m.quantization.name.lower())
            or (m.architecture and self.current_filter in m.architecture.lower())
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
            self.post_highlighted_model(None)

    # ======= ACTIONS =======

    def action_cursor_up(self) -> None:
        self.table.action_cursor_up()

    def action_cursor_down(self) -> None:
        self.table.action_cursor_down()

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

    # ======= EVENTS =======

    @on(DataTable.RowHighlighted)
    def handle_row_highlight(self, event: DataTable.RowHighlighted) -> None:
        """Fires when navigating through table."""
        if not self.has_focus_within or not self.table.row_count > 0:
            return

        key = event.row_key.value
        assert key
        model = self._all_models.get(key)
        self.post_message(self.post_highlighted_model(model))

    @on(DescendantFocus)
    def on_table_focus(self) -> None:
        """Restore cursor and re-emit selection when table gains focus."""
        self.table.show_cursor = True

        if self.table.row_count > 0 and self.table.cursor_row is not None:
            cell_key = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
            row_key = cell_key.row_key.value
            if row_key and row_key in self._all_models:
                self.post_message(
                    self.post_highlighted_model(self._all_models[row_key])
                )
            else:
                self.post_message(self.post_highlighted_model(None))

    @on(DescendantBlur)
    def on_table_blur(self) -> None:
        """Hide table cursor when focus moves to another pane."""
        self.table.show_cursor = False


# Model DataTable implementations


class DownloadedModels(BaseModelTable):
    """Widget displaying all downloaded models available on the server."""

    def __init__(self, **kwargs) -> None:
        super().__init__(table_id="dl-models-table", **kwargs)


# TODO: Decide if I need to keep this class for anything
# class LoadedModels(BaseModelTable):
#     """Widget displaying currently loaded models for immediate use."""
#     def __init__(self, **kwargs) -> None:
#         super().__init__(table_id="loaded-models-table", **kwargs)


# OptionList for Context Pane and maybe Loaded Models pane
class ModelInstanceTable(DataTable):
    """Widget to display current running instances and associated context."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.add_column(label="Instance ID", width=32)
        self.add_column(label="Context")
        self.show_horizontal_scrollbar = False
        self.cursor_type = "row"
