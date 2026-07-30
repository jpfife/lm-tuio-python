"""Primary application interface and management screen.

Container for interactive and display components.
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Input, Footer

from lm_tuio.components import (
    ActionLog,
    ConnectionStatus,
    ContextPane,
    DownloadedModels,
    LoadedModels,
    Title,
)
from lm_tuio.config import AppConfig
from lm_tuio.screens.server_select import ServerSelectionModal


class DashboardScreen(Screen):
    """Primary application dashboard."""

    BINDINGS = [
        ("q,escape", "quit", "[quit]"),
        ("c", "change_server", "[change server]"),
        ("r", "refresh_models", "[refresh models]"),
        ("/", "filter", "[filter]"),
        ("*", "retry_connection"),
    ]

    def compose(self) -> ComposeResult:
        # Set widget instances
        self.connection_widget: ConnectionStatus = ConnectionStatus(
            "Connection Status", id="conn-status", classes="box"
        )
        self.connection_widget.border_title = self.connection_widget.name

        self.title_widget: Title = Title(
            "LM Studio Dashboard", id="logo-title", classes="box"
        )
        self.title_widget.border_subtitle = self.title_widget.name

        self.actionlog_widget: ActionLog = ActionLog(
            name="Actions / Logs",
            id="action-log",
            classes="box",
        )
        self.actionlog_widget.border_title = self.actionlog_widget.name

        self.loadedmodels_widget: LoadedModels = LoadedModels(
            name="Actively Loaded Models",
            id="loaded-models",
            classes="box",
        )
        self.loadedmodels_widget.border_title = self.loadedmodels_widget.name

        self.downloadedmodels_widget: DownloadedModels = DownloadedModels(
            name="Downloaded Models",
            id="downloaded-models",
            classes="box",
        )
        self.downloadedmodels_widget.border_title = self.downloadedmodels_widget.name

        self.contextpane_widget: ContextPane = ContextPane(
            name="Details",
            id="context-pane",
            classes="box",
        )
        self.contextpane_widget.border_title = self.contextpane_widget.name

        self.search_bar: Input = Input(
            "Set list filter, ESC to cancel",
            name="Filter",
            id="search-bar",
            classes="footers hidden",
        )
        self.search_bar.border_title = self.search_bar.name

        # Top row telemetry and logging
        with Horizontal(id="header-zone"):
            yield self.connection_widget
            yield self.title_widget
            yield self.actionlog_widget

        # Middle row for main application content
        with Horizontal(id="main-zone"):
            yield self.loadedmodels_widget
            yield self.downloadedmodels_widget
            yield self.contextpane_widget

        # Bottom row hotkeys bar
        yield Footer(id="main-footer", classes="footers")
        yield self.search_bar

    # ========== ACTIONS ==========

    def action_filter(self) -> None:
        """Default hotkey '/' to filter display lists"""

    def action_quit(self) -> None:
        """Default hotkey 'q' to quit application"""
        self.app.exit()

    def action_change_server(self) -> None:
        """Default hotkey 'c' to connect to server"""
        self.app.push_screen(
            ServerSelectionModal(), callback=self.connection_widget.apply_new_server
        )

    def action_retry_connection(self) -> None:
        """Default hotkey '*' to retest connection to API endpoint"""
        self.notify(
            "Retesting connection to server...", timeout=AppConfig.NOTIFY_TIMEOUT
        )
        self.connection_widget.reset_status()
        self.connection_widget.update_connection_status()

    # ========= EVENTS ==========
