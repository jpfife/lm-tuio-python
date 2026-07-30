"""Dynamic widget to display relevant information for dashboard focus item."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Static

from lm_tuio.models import ModelInfo


class ContextPane(Static):
    """Dynamic details pane for selected dashboard information."""

    def __init__(self):
        # Initialize static labels
        self.ctx_placeholder: Label = Label(
            "Select model to view details.", id="ctx-placeholder"
        )
        self.ctx_name: Label = Label("Model", id="ctx-name")
        self.ctx_publisher: Label = Label("Publisher", id="ctx-publisher")
        self.ctx_arch: Label = Label("Architecture", id="ctx-arch")
        self.ctx_context: Label = Label("Context", id="ctx-context")
        self.ctx_quant: Label = Label("Quantization", id="ctx-quant")

        # Initialize dynamic content labels
        self.ctx_name_val: Label = Label("", id="ctx-name_val")
        self.ctx_publisher_val: Label = Label("", id="ctx-publisher_val")
        self.ctx_arch_val: Label = Label("", id="ctx-arch_val")
        self.ctx_context_val: Label = Label("", id="ctx-context_val")
        self.ctx_quant_val: Label = Label("", id="ctx-quant_val")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield self.ctx_placeholder

            yield self.ctx_name
            yield self.ctx_name_val

            yield self.ctx_publisher
            yield self.ctx_publisher_val

            yield self.ctx_arch
            yield self.ctx_arch_val

            yield self.ctx_context
            yield self.ctx_context_val

            yield self.ctx_quant
            yield self.ctx_quant_val

    def on_mount(self) -> None:
        pass

    def update_model_context(self, model: ModelInfo | None) -> None:
        """Update context value fields based on highlighted model"""
        labels = self.query(Label).exclude("#ctx-placeholder")

        # Clear if no model highlighted
        if not model:
            self.ctx_placeholder.display = True
            for label in labels:
                label.display = False
            return

        self.ctx_placeholder.display = False
        for label in labels:
            label.display = True

        # Populate value labels
        self.ctx_name_val.update(f"{model.display_name}")
        self.ctx_publisher_val.update(f"{model.publisher}")
        self.ctx_arch_val.update(f"{model.architecture}")
        self.ctx_context_val.update(f"{model.max_context_length}")

        quant = f"{model.quantization.bits_per_weight}" if model.quantization else None
        if quant:
            self.ctx_quant_val.update(quant)
