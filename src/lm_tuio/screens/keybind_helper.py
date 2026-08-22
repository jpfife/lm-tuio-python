"""Static modal refernce screen to display all currently set keybinds."""

from typing import Any

from rich.table import Table
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, Static

from lm_tuio.config import KeymapManager


class KeybindSection(Static):
    """Renders single TOML table section from keymap config file."""

    def __init__(self, title: str, bindings_data: dict[str, Any]) -> None:
        super().__init__()
        self.section_title = title
        self.bindings_data = bindings_data

    def render(self) -> Table:
        """Builds a two-column table for each section in keymap config file."""
        table = Table(
            title=f"[bold cyan][ {self.section_title} ][/]".replace("_", " "),
            title_justify="left",
            box=None,
            expand=True,
            padding=(0, 1),
        )

        table.add_column("Description", style="dim", ratio=1)
        table.add_column("Key(s)", style="bold yellow", justify="right")

        for action_name, config in self.bindings_data.items():
            desc = config.get("desc", action_name)
            keys = config.get("keys", [])

            if isinstance(keys, str):
                keys = [keys]

            formatted_keys = (
                " / ".join(f"[green]{k}[/]" for k in keys)
                .replace("left_square_bracket", "[")
                .replace("right_square_bracket", "]")
            )
            formatted_desc = desc.replace("<", "").replace(">", "")

            table.add_row(formatted_desc, formatted_keys)

        return table


class KeybindsModal(ModalScreen):
    """A floating modal screen displaying all app keybinds."""

    BINDINGS = [
        Binding("q,escape,?", "dismiss_modal", "<close>", show=True),
        Binding("up,k,alt+p", "scroll_up", "<scroll up>", show=True),
        Binding("down,j,alt+n", "scroll_down", "<scroll down>", show=True),
    ]

    explanation: str = "General navigation with 'Tab' to move between panes and arrow keys within panes.\nVIM-style window/selections are available for more precise movement control using 'ctrl+h/j/k/l' to move between panes and 'h/j/k/l' within panes.\nUse 'alt+h/j/k/l/p/n' instead if terminal emulators/multiplexers are swallowing inputs."

    def compose(self) -> ComposeResult:
        keymap = KeymapManager.load_keymap()
        self.scroller: VerticalScroll = VerticalScroll(id="keybind-dialog")

        with self.scroller:
            yield Label("Application Keybinds", id="keybind-title")
            yield Label(self.explanation, id="keybind-explaner", classes="comments")

            with Grid(id="keybind-grid"):
                for scope, actions in keymap.items():
                    yield KeybindSection(scope, actions)

            yield Footer(id="keybinds-footer")

    def action_dismiss_modal(self) -> None:
        self.dismiss()

    def action_scroll_up(self) -> None:
        self.scroller.scroll_up()

    def action_scroll_down(self) -> None:
        self.scroller.scroll_down()
