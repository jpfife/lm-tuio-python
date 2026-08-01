"""Dynamic widget to display relevant information for dashboard focus item."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, Static, OptionList

from lm_tuio.models import ModelInfo, estimate_context_cache_memory, format_bytes


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
        self.ctx_loaded_insts_ids: Label = Label(
            "Instance IDs:",
            id="ctx-loaded-insts-ids",
            classes="ctx-titles hidden",
        )
        self.ctx_loaded_context: Label = Label(
            "Context:",
            id="ctx-loaded-context",
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
        self.ctx_loaded_insts_ids_val: Label = Label(
            "", id="ctx-loaded-insts-ids-val", classes="ctx-values hidden"
        )
        self.ctx_loaded_context_val: Label = Label(
            "", id="ctx-loaded-context-val", classes="ctx-values hidden"
        )
        self.ctx_total_memory_val: Label = Label(
            "", id="ctx-total-memory-val", classes="ctx-values hidden"
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
                with Vertical():
                    yield self.ctx_loaded_insts_ids
                    yield self.ctx_loaded_insts_ids_val

                with Vertical():
                    yield self.ctx_loaded_context
                    yield self.ctx_loaded_context_val

    def on_mount(self) -> None:
        separator = self.query_one("#ctx-separator", Horizontal)
        separator.border_title = " Loaded "

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

        # Populate base model info value labels
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

        # Populate loaded instance information labels
        self.ctx_num_loaded_insts_val.update(f"{len(model.loaded_instances)}")

        if not model.loaded_instances:
            self.ctx_loaded_insts_ids_val.update("")
            self.ctx_loaded_context_val.update("")
            self.ctx_total_memory_val.update("")
            return

        size_bytes: int = model.size_bytes * len(model.loaded_instances)
        context_bytes: int = 0
        ids_str: str = ""
        ctx_str: str = ""
        for mdl in model.loaded_instances:
            if len(mdl.id) > 23:
                ids_str += f"...{mdl.id[-20:]}\n"
            else:
                ids_str += f"{mdl.id}\n"

            ctx_str += f"{format_bytes(mdl.config.context_length)} ({mdl.config.context_length})\n"

            context_bytes += estimate_context_cache_memory(
                model.size_bytes, mdl.config.context_length
            )

        self.ctx_loaded_insts_ids_val.update(ids_str)
        self.ctx_loaded_context_val.update(ctx_str)

        memory_str: str = (
            f"{format_bytes(size_bytes)} (Models)\n\nWith KV Cache context:"
        )
        memory_str += f"\nKV Q16\t~ {format_bytes(context_bytes + size_bytes)}"
        memory_str += f"\nKV Q8\t~ {format_bytes((context_bytes // 2) + size_bytes)}"
        memory_str += f"\nKV Q4\t~ {format_bytes((context_bytes // 4) + size_bytes)}"
        memory_str += f"\nKV Q2\t~ {format_bytes((context_bytes // 8) + size_bytes)}"

        self.ctx_total_memory_val.update(memory_str)
