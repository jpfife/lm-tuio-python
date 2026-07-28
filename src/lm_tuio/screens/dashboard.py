"""Primary application interface and management screen.

Container for interactive and display components.
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer

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
        ("q", "quit", "[quit]"),
        ("c", "change_server", "[change server]"),
        ("r", "refresh_models", "[refresh models]"),
        ("*", "retry_connection"),
    ]

    # TODO: Set relevant values
    def compose(self) -> ComposeResult:
        # Set widget instances
        self.connection_widget: ConnectionStatus = ConnectionStatus(
            "Connectivity Status", id="conn-status", classes="box"
        )

        self.title_widget: Title = Title(
            "LM TUIO Logo\nLM Studio Dashboard", id="logo-title", classes="box"
        )
        self.title_widget.border_subtitle = "LM Studio Dashboard"

        self.actionlog_widget: ActionLog = ActionLog(
            name="Action Log",
            id="action-log",
            classes="box",
        )
        self.actionlog_widget.border_title = "Log / Actions"

        self.loadedmodels_widget: LoadedModels = LoadedModels(
            name="Actively Loaded Models",
            id="loaded-models",
            classes="box",
        )
        self.loadedmodels_widget.border_title = "Loaded Models"

        self.downloadedmodels_widget: DownloadedModels = DownloadedModels(
            name="Downloaded Models",
            id="downloaded-models",
            classes="box",
        )
        self.downloadedmodels_widget.border_title = "Downloaded Models"

        self.contextpane_widget: ContextPane = ContextPane(
            name="Dynamic Context Pane",
            id="context-pane",
            classes="box",
        )
        self.contextpane_widget.border_title = "Details"

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
        yield Footer()

    # ========== ACTIONS ==========

    def action_quit(self) -> None:
        """Triggered by 'q' hotkey"""
        self.app.exit()

    def action_change_server(self) -> None:
        """Triggered by 'c' hotkey"""
        net_config: AppConfig = AppConfig()
        net_config.load()
        loaded_ip: str = net_config.target
        loaded_port: int = net_config.port
        loaded_subnet: str = net_config.scan_subnet

        def apply_new_server(ip_conf: tuple[str, int] | None) -> None:
            if not ip_conf:
                return

            ip, port = ip_conf
            self.connection_widget.server_ip = ip
            self.connection_widget.server_port = port
            self.notify(
                f"Connecting to {ip}:{port}...", timeout=AppConfig.NOTIFY_TIMEOUT
            )
            self.connection_widget.reset_status()
            self.connection_widget.update_connection_status()

        self.app.push_screen(
            ServerSelectionModal(loaded_ip, loaded_port, loaded_subnet),
            callback=apply_new_server,
        )

    def action_retry_connection(self) -> None:
        """Triggered by '*' hotkey"""
        self.notify(
            "Retesting connection to server...", timeout=AppConfig.NOTIFY_TIMEOUT
        )
        self.connection_widget.reset_status()
        self.connection_widget.update_connection_status()

    # ========= EVENTS ==========

    # TODO: Add handler for downloadedmodels_widget to refresh list
