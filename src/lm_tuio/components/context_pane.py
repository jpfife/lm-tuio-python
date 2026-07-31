"""Dynamic widget to display relevant information for dashboard focus item."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, Static

from lm_tuio.models import ModelInfo, format_bytes


class ContextPane(Static):
    """Dynamic details pane for selected dashboard information."""

    def __init__(self, *args, **kwargs):
        # Initialize static labels
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

        # Initialize dynamic content labels
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

        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(id="context-details-pane"):
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

        # Populate value labels
        self.ctx_name_val.update(f"{model.key}")
        self.ctx_publisher_val.update(f"{model.publisher}")
        self.ctx_arch_val.update(f"{model.architecture}")
        self.ctx_max_context_val.update(f"{format_bytes(model.max_context_length)}")

        quant = (
            f"{model.quantization.bits_per_weight}-bit:\n{model.quantization.name}"
            if model.quantization
            else None
        )
        if quant:
            self.ctx_quant_val.update(quant)
