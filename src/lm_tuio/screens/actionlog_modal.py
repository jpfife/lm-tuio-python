"""Pop-out modal for viewing and copying full application action log."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, RichLog

from lm_tuio.components.action_log import LogColor
from lm_tuio.config import keymap


class ActionLogModal(ModalScreen[None]):
    """A larger, scrollable view of the ActionLog with clipboard support."""

    BINDINGS = keymap.KeymapManager.get_bindings("action_log_viewer")

    def __init__(self, history: list[tuple[str, str, str]], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.history = history

    def compose(self) -> ComposeResult:
        with Vertical(id="action-log-modal-dialog"):
            yield Label("Action Log Viewer", id="action-log-modal-title")

            self.log_viewer = RichLog(
                highlight=True, markup=True, wrap=True, id="action-log-viewer"
            )
            yield self.log_viewer

            yield Footer()

    def on_mount(self) -> None:
        """Pre-populate log viewer with the existing dashboard history."""

        for timestamp, severity, message in self.history:
            match severity.lower():
                case "error" | "err":
                    tag = f"{LogColor.ERR}ERR[/]"
                case "warning" | "warn":
                    tag = f"{LogColor.WARN}WRN[/]"
                case "success" | "ok":
                    tag = f"{LogColor.OK}OK [/]"
                case _:
                    tag = f"{LogColor.INF}INF[/]"

            self.log_viewer.write(f"[dim]{timestamp}[/] {tag} {message}")

    def action_quit(self) -> None:
        self.dismiss(None)

    def action_copy_to_clipboard(self) -> None:
        """Strip markup and copy plaintext history to system clipboard."""
        plain_text_lines = []
        for timestamp, severity, message in self.history:
            sanitized_sev = severity.upper()[:3]
            plain_text_lines.append(f"[{timestamp}] {sanitized_sev}: {message}")

        full_text = "\n".join(plain_text_lines)

        self.app.copy_to_clipboard(full_text)
        self.notify("Action log copied to system clipboard", severity="information")

    def action_scroll_up(self) -> None:
        self.log_viewer.scroll_up()

    def action_scroll_down(self) -> None:
        self.log_viewer.scroll_down()
