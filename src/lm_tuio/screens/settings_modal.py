"""Settings modal for configuring application preferences.

Saves config to config.toml in user's configuration directory.
"""

from zoneinfo import available_timezones

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, Select

from lm_tuio.config import KeymapManager
from lm_tuio.events import SettingsSaved


class SettingsScreen(ModalScreen[tuple[str, str]]):
    """Modal dialog for application settings (theme, timezone)."""

    BINDINGS = KeymapManager.get_bindings("settings_screen")

    def __init__(self, theme: str, timezone: str) -> None:
        super().__init__()
        self._config_theme = theme
        self._pending_theme = theme
        self._config_timezone = timezone
        self._pending_timezone = timezone

    def compose(self) -> ComposeResult:
        theme_options: list[tuple[str, str]] = [
            ("ANSI Dark", "ansi-dark"),
            ("ANSI Light", "ansi-light"),
            ("Atom One Dark", "atom-one-dark"),
            ("Atom One Light", "atom-one-light"),
            ("Catppuccin Frappe", "catppuccin-frappe"),
            ("Catppuccin Latte", "catppuccin-latte"),
            ("Catppuccin Macchiato", "catppuccin-macchiato"),
            ("Catppuccin Mocha", "catppuccin-mocha"),
            ("Dracula", "dracula"),
            ("Flexoki", "flexoki"),
            ("Gruvbox", "gruvbox"),
            ("Monokai", "monokai"),
            ("Nord", "nord"),
            ("Rose Pine", "rose-pine"),
            ("Rose Pine Dawn", "rose-pine-dawn"),
            ("Rose Pine Moon", "rose-pine-moon"),
            ("Solarized Dark", "solarized-dark"),
            ("Solarized Light", "solarized-light"),
            ("Textual Dark", "textual-dark"),
            ("Textual Light", "textual-light"),
            ("Tokyo Night", "tokyo-night"),
        ]

        tz_options: list[tuple[str, str]] = [
            (tz, tz) for tz in sorted(available_timezones()) if tz
        ]

        self.theme_select: Select[str] = Select(
            options=theme_options,
            value=self._config_theme,
            id="settings-theme-select",
        )
        self.timezone_select: Select[str] = Select(
            options=tz_options,
            value=self._config_timezone,
            id="settings-timezone-select",
        )

        with Vertical():
            yield Label("Theme", id="label-theme")
            yield self.theme_select
            yield Label("Timezone", id="label-timezone")
            yield self.timezone_select
        with Horizontal(id="btn-row"):
            yield Button("Save", variant="success", id="btn-save")
            yield Button("Cancel", variant="error", id="btn-cancel")

        yield Footer()

    def on_mount(self) -> None:
        """Focus the theme selector on open."""
        self.theme_select.focus()

    # ======= EVENTS =======

    @on(Select.Changed, "#settings-theme-select")
    def on_theme_changed(self, event: Select.Changed) -> None:
        """Apply theme immediately when user selects from dropdown."""
        self._pending_theme = str(event.value)
        self.app.theme = self._pending_theme

    @on(Button.Pressed, "#btn-save")
    def on_save(self) -> None:
        """Save settings and dismiss with new values."""
        self._pending_timezone = str(self.timezone_select.value)
        self.dismiss((self._pending_theme, self._pending_timezone))

    @on(Button.Pressed, "#btn-cancel")
    def on_cancel(self) -> None:
        """Cancel and revert theme to config value."""
        self.app.theme = self._config_theme
        self.dismiss((self._config_theme, self._config_timezone))

    def action_dismiss_modal(self) -> None:
        """Cancel and dismiss modal."""
        self.app.theme = self._config_theme
        self.dismiss((self._config_theme, self._config_timezone))
