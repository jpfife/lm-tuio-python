"""Dynamic widget to display relevant information for dashboard focus item."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Label, Static

from lm_tuio.models import (
    ModelInfo,
    estimate_context_cache_memory,
    format_bytes,
    ModelInstanceTable,
)


class ContextPane(Static):
    """Dynamic details pane for selected dashboard information."""

    def __init__(self, *args, **kwargs):
        # Initialize static labels, base model details (top) section
        self.ctx_placeholder: Label = Label(
            "Select model to view details.", id="ctx-placeholder"
        )
        self.ctx_name: Label = Label(
            "Model Key", id="ctx-name", classes="ctx-titles hidden"
        )
        self.ctx_publisher: Label = Label(
            "Publisher", id="ctx-publisher", classes="ctx-titles hidden"
        )
        self.ctx_arch: Label = Label(
            "Architecture", id="ctx-arch", classes="ctx-titles hidden"
        )
        self.ctx_max_context: Label = Label(
            "Max Context", id="ctx-max-context", classes="ctx-titles hidden"
        )
        self.ctx_quant: Label = Label(
            "Quantization", id="ctx-quant", classes="ctx-titles hidden"
        )

        # Initialize static labels, loaded model details (bottom) section
        self.ctx_num_loaded_insts: Label = Label(
            "Loaded Instances:",
            id="ctx-num-loaded-insts",
            classes="ctx-titles hidden",
        )
        self.ctx_total_memory: Label = Label(
            "Total Memory (Est):",
            id="ctx-total-memory",
            classes="ctx-titles hidden",
        )

        # Initialize dynamic content labels, base model details (top) section
        self.ctx_name_val: Label = Label(
            "", id="ctx-name_val", classes="ctx-values hidden"
        )
        self.ctx_publisher_val: Label = Label(
            "", id="ctx-publisher_val", classes="ctx-values hidden"
        )
        self.ctx_arch_val: Label = Label(
            "", id="ctx-arch_val", classes="ctx-values hidden"
        )
        self.ctx_max_context_val: Label = Label(
            "", id="ctx-max-context_val", classes="ctx-values hidden"
        )
        self.ctx_quant_val: Label = Label(
            "", id="ctx-quant_val", classes="ctx-values hidden"
        )

        # Initialize dynamic content value labels, loaded model(s) details (bottom) section
        self.ctx_num_loaded_insts_val: Label = Label(
            "", id="ctx-num-loaded-insts-val", classes="ctx-values hidden"
        )
        self.ctx_total_memory_val: Label = Label(
            "", id="ctx-total-memory-val", classes="ctx-values hidden"
        )

        self.ctx_insts_table: ModelInstanceTable = ModelInstanceTable(
            id="ctx-insts-table"
        )

        super().__init__(*args, **kwargs)

    # Present base Model details in top section, loaded instance info in bottom
    def compose(self) -> ComposeResult:
        with Vertical(id="context-details-pane"):
            # Model base details, top context section
            yield self.ctx_placeholder

            yield self.ctx_name
            yield self.ctx_name_val

            with Horizontal(id="ctx-pub-arch-details", classes="ctx-horizontal-group"):
                with Vertical():
                    yield self.ctx_publisher
                    yield self.ctx_publisher_val
                with Vertical():
                    yield self.ctx_arch
                    yield self.ctx_arch_val

            with Horizontal(
                id="ctx-context-quant-details", classes="ctx-horizontal-group"
            ):
                with Vertical():
                    yield self.ctx_max_context
                    yield self.ctx_max_context_val

                with Vertical():
                    yield self.ctx_quant
                    yield self.ctx_quant_val

            yield Horizontal(id="ctx-separator")

            # Model loaded instances information, bottom section
            with Horizontal():
                with Vertical():
                    yield self.ctx_num_loaded_insts
                    yield self.ctx_num_loaded_insts_val

                with Vertical():
                    yield self.ctx_total_memory
                    yield self.ctx_total_memory_val

            with Horizontal(
                id="ctx-loaded-insts-details", classes="ctx-horizontal-group"
            ):
                yield self.ctx_insts_table

    def on_mount(self) -> None:
        separator = self.query_one("#ctx-separator", Horizontal)
        separator.border_title = " Loaded "

    def _update_base_model_info(self, model: ModelInfo) -> None:
        """Helper to update base model details pane widgets."""

        self.ctx_name_val.update(f"{model.key}")
        self.ctx_publisher_val.update(f"{model.publisher}")
        self.ctx_arch_val.update(f"{model.architecture}")
        self.ctx_max_context_val.update(f"{format_bytes(model.max_context_length)}")

        quant = (
            f"{model.quantization.bits_per_weight}-bit: {model.quantization.name}"
            if model.quantization
            else None
        )
        if quant:
            self.ctx_quant_val.update(quant)

        self.ctx_num_loaded_insts_val.update(f"{len(model.loaded_instances)}")

    def _update_loaded_model_info(self, model: ModelInfo) -> None:
        """Helper to update loaded model instance details pane widgets."""

        size_bytes: int = model.size_bytes * len(model.loaded_instances)
        context_bytes: int = 0
        ids_str: str = ""
        ctx_str: str = ""
        for mdl in model.loaded_instances:
            if len(mdl.id) > 30:
                ids_str = f"...{mdl.id[-27:]}"
            else:
                ids_str = f"{mdl.id}"

            ctx_str = f"{format_bytes(mdl.config.context_length)} ({mdl.config.context_length})"

            context_bytes += estimate_context_cache_memory(
                model.size_bytes, mdl.config.context_length
            )

            self.ctx_insts_table.add_row(ids_str, ctx_str)

        memory_str: str = (
            f"{format_bytes(size_bytes)} (Models)\n\nWith KV Cache context:"
        )
        memory_str += f"\nKV Q16\t~ {format_bytes(context_bytes + size_bytes)}"
        memory_str += f"\nKV Q8\t~ {format_bytes((context_bytes // 2) + size_bytes)}"
        memory_str += f"\nKV Q4\t~ {format_bytes((context_bytes // 4) + size_bytes)}"

        self.ctx_total_memory_val.update(memory_str)

    def update_model_context(self, model: ModelInfo | None) -> None:
        """Update context value fields based on highlighted model"""
        labels = self.query(Label).exclude("#ctx-placeholder")

        # Clear if no model highlighted
        if not model:
            self.ctx_placeholder.update("Highlight model to view details")
            for label in labels:
                label.display = False
            return

        self.ctx_placeholder.update(f"{model.display_name}")
        for label in labels:
            label.display = True

        self._update_base_model_info(model)

        if not model.loaded_instances:
            self.ctx_total_memory_val.update("")
            self.ctx_insts_table.clear()
            return

        self._update_loaded_model_info(model)
