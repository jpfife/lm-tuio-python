"""Load Model modal to fire load API request to LMS endpoint with selected parameters."""

from typing import Any

from textual import on
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Collapsible, Footer, Input, Label, Static

from lm_tuio.models import ModelInfo, estimate_context_cache_memory, format_bytes


class LoadModelModal(ModalScreen[dict[str, Any] | None]):
    """Modal dialog for configuring parameters before loading a model via REST API."""

    BINDINGS = [
        Binding("q,escape", "dismiss_modal", "<cancel>", show=True),
        Binding("l", "submit_load_model", "<load>", show=True),
    ]

    current_context: reactive[int]
    default_ctx: int

    def __init__(self, model: ModelInfo) -> None:
        super().__init__()
        self.model = model
        self.model_id = getattr(model, "key", None)
        self.model_type = getattr(model, "type", "llm").lower()
        self.max_context = getattr(model, "max_context_length", (32 * 1024))
        if not self.max_context or self.max_context <= 0:
            self.max_context = 32 * 1024

    def compose(self) -> ComposeResult:
        self.default_ctx = min((32 * 1024), self.max_context)

        with VerticalScroll(id="load-modal-dialog"):
            yield Label(f"Load Model: {self.model_id}", id="load-modal-title")

            # Model type and defaults toggle
            with Horizontal(id="load-modal-top-bar"):
                yield Label(
                    f"Type: [bold accent]{self.model_type.upper()}[/]",
                    id="model-type-badge",
                )
                yield Checkbox(
                    "Use Server Defaults",
                    value=True,
                    id="check-defaults",
                )

            # Universal params
            with Vertical(classes="form-section", id="manual-params-section"):
                yield Label("Context Length (Tokens):", classes="input-label")
                with Horizontal():
                    yield Checkbox(
                        "Override Context Size",
                        value=False,
                        id="check-context-override",
                        disabled=False,
                    )
                    yield Input(
                        value="0",
                        placeholder=f"Max: {self.max_context}",
                        id="input-context-length",
                        type="integer",
                        disabled=True,  # Opt for LMS config by default
                    )
                with Horizontal(id="context-details-group"):
                    with Vertical():
                        yield Label(
                            "Model Size:",
                            id="load-model-size-label",
                            classes="section-title",
                        )
                        yield Label("", id="load-model-size-val")

                    with Vertical():
                        yield Label(
                            "KV Cache RAM (Estimated):",
                            id="load-model-kv-cache-label",
                            classes="section-title",
                        )
                        yield Label("", id="load-model-kv-cache-val")

                # Dynamic Context Length Progress Bar
                yield Label("Context Override Size")
                yield ContextProgressBar(
                    current=self.default_ctx,
                    max_val=self.max_context,
                    id="context-progress-bar",
                )

            # Advanced options (Override enabled)
            with Collapsible(
                title="Advanced Engine Settings (LLM)",
                id="llm-advanced-section",
                collapsed=True,
                disabled=True,
            ):
                with Grid(id="checkbox-grid"):
                    yield Checkbox(
                        "Flash Attention",
                        value=True,
                        id="check-flash-attention",
                    )
                    yield Checkbox(
                        "Offload KV Cache to GPU",
                        value=True,
                        id="check-kv-offload",
                    )

                yield Label("Eval Batch Size:", classes="input-label")
                yield Input(
                    value="512",
                    placeholder="512",
                    id="input-eval-batch",
                    type="integer",
                )

                yield Label("Num Experts (MoE only):", classes="input-label")
                yield Input(
                    placeholder="Leave blank if not MoE",
                    id="input-num-experts",
                    type="integer",
                )

            # Buttons
            with Horizontal(id="load-btn-group"):
                yield Button("Load Model", variant="success", id="btn-load-submit")
                yield Button("Cancel", variant="error", id="btn-load-cancel")

            yield Footer()

    def on_mount(self) -> None:
        """Hide advanced LLM options completely if an embedding model is selected."""
        self.query_one("#check-defaults").focus()

        if self.model_type == "embedding":
            self.query_one("#llm-advanced-section").display = False

        self.query_one("#load-model-size-val", Label).update(
            format_bytes(self.model.size_bytes)
        )

    # ======= ACTIONS =======

    def action_dismiss_modal(self) -> None:
        """Cancel and dismiss modal."""
        self.dismiss(None)

    def action_submit_load_model(self) -> None:
        self.handle_submit()

    # ======= EVENTS =======

    @on(Checkbox.Changed, "#check-defaults")
    def handle_defaults_toggle(self, event: Checkbox.Changed) -> None:
        """Enable or disable input controls based on whether override is checked."""
        advanced_section = self.query_one("#llm-advanced-section")
        advanced_section.disabled = not event.value

    @on(Checkbox.Changed, "#check-context-override")
    def handle_context_override_toggle(self, event: Checkbox.Changed) -> None:
        ctx_input = self.query_one("#input-context-length", Input)
        ctx_input.disabled = not event.value
        if ctx_input.disabled:
            ctx_input.value = "0"
        else:
            ctx_input.value = str(self.default_ctx)

    @on(Input.Changed, "#input-context-length")
    def handle_context_changed(self, event: Input.Changed) -> None:
        """Update the ASCII context progress bar in real time."""
        val_str: str = event.value.strip()
        new_val: int = int(val_str) if val_str.isdigit() else 0
        new_val = min(new_val, self.max_context)

        self.query_one("#input-context-length", Input).value = str(new_val)
        self.query_one(ContextProgressBar).current_context = new_val

        self._update_context_memory(new_val)

    @on(Button.Pressed, "#btn-load-cancel")
    def handle_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-load-submit")
    def handle_submit(self) -> None:
        """Build the API payload and pass it back to Dashboard via dismiss callback."""
        use_defaults = self.query_one("#check-defaults", Checkbox).value
        override_context = self.query_one("#check-context-override", Checkbox).value

        payload: dict[str, Any] = {
            "model": self.model_id,
            "echo_load_config": True,
        }

        if not use_defaults:
            ctx_val = self.query_one("#input-context-length", Input).value.strip()
            if ctx_val.isdigit():
                payload["context_length"] = int(ctx_val)

            if self.model_type != "embedding":
                payload["flash_attention"] = self.query_one(
                    "#check-flash-attention", Checkbox
                ).value
                payload["offload_kv_cache_to_gpu"] = self.query_one(
                    "#check-kv-offload", Checkbox
                ).value

                eval_batch = self.query_one("#input-eval-batch", Input).value.strip()
                if eval_batch.isdigit():
                    payload["eval_batch_size"] = int(eval_batch)

                experts = self.query_one("#input-num-experts", Input).value.strip()
                if experts.isdigit():
                    payload["num_experts"] = int(experts)

        elif override_context:
            ctx_val = self.query_one("#input-context-length", Input).value.strip()
            if ctx_val.isdigit():
                payload["context_length"] = int(ctx_val)

        self.dismiss(payload)

    def _update_context_memory(self, current: int) -> None:
        context_bytes = estimate_context_cache_memory(self.model.size_bytes, current)

        kv_mem_str: str = (
            f"KV Q16 - {format_bytes(context_bytes + self.model.size_bytes)}\n"
        )
        kv_mem_str += (
            f"KV Q8  - {format_bytes((context_bytes // 2) + self.model.size_bytes)}\n"
        )
        kv_mem_str += (
            f"KV Q4  - {format_bytes((context_bytes // 4) + self.model.size_bytes)}"
        )

        self.query_one("#load-model-kv-cache-val", Label).update(kv_mem_str)


class ContextProgressBar(Static):
    """Reactive 'progress bar' to show selected vs max context size."""

    current_context: reactive[int] = reactive(0)
    max_context: reactive[int] = reactive(32768)

    def __init__(self, current: int, max_val: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.current_context = current
        self.max_context = max_val

    def render(self) -> str:
        max_val = max(self.max_context, 1)
        current = min(max(self.current_context, 0), max_val)

        width = 24
        ratio = current / max_val
        filled = int(ratio * width)
        empty = width - filled

        max_label = f"{max_val // 1024}K" if max_val >= 1024 else str(max_val)
        return (
            f"[dim]0[/] <[bold green]{'=' * filled}[/]"
            f"[dim]{'-' * empty}[/]> [bold cyan]{max_label}[/]"
        )
