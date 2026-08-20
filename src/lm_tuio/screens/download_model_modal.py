"""Modal for triggering API model downloads.

Accepts model catalog identifiers and direct HuggingFace links, e.g.:
- openai/gpt-oss-20b
- https://huggingface.co/lmstudio-community/gpt-oss-20b-GGUF
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label

from lm_tuio.config import keymap


class DownloadModelModal(ModalScreen[str | None]):
    """Capture model download target and pass back to Dashboard."""

    BINDINGS = keymap.KeymapManager.get_bindings("download_models")

    explainer: str = "Enter a direct HuggingFace URL or LM Studio model catalog ID. Example:\n\thttps://huggingface.co/lmstudio-community/gpt-oss-20b-GGUF or\n\topenai/gpt-oss-20b"

    def compose(self) -> ComposeResult:
        self.download_model_input: Input = Input(
            placeholder=r"https://huggingface.co/lmstudio-community/gpt-oss-20b-GGUF",
            id="input-download-target",
        )

        with Vertical(id="download-modal-dialog"):
            yield Label(
                "Download Model from HuggingFace",
                id="download-modal-title",
                classes="section-title",
            )
            yield Label(
                content=self.explainer,
                id="download-modal-explainer",
                classes="comments",
            )
            yield self.download_model_input

            with Horizontal(classes="dl-button-group"):
                yield Button("Download", variant="success", id="btn-submit-dl")
                yield Button("Cancel", variant="error", id="btn-cancel-dl")

            yield Footer()

    @on(Button.Pressed, "#btn-cancel-dl")
    def action_quit(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-submit-dl")
    @on(Input.Submitted, "#input-download-target")
    def handle_submit(self) -> None:
        target = self.download_model_input.value.strip()
        if target:
            self.dismiss(target)
