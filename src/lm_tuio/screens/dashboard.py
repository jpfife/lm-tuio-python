from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal
from textual.widgets import Static, Footer

from lm_tuio.components import ActionLog, ConnectionStatus, ContextPane, DownloadedModels, Title, LoadedModels

class DashboardScreen(Screen):
    '''Primary dashboard.'''
    BINDINGS = [
        ('q', 'quit', '[quit]'),
        ('r', 'refresh_models', '[refresh models]'),
        ('s', 'change_server', '[change server]'),
        ('c', 'retry_connection'),
    ]

    def compose(self) -> ComposeResult:
        # Set widget instances
        self.connection_widget: ConnectionStatus = ConnectionStatus(
            'Connectivity Status',
            id='conn-status',
            classes='box'
        )
        self.title_widget: Title = Title(
            'LM TUIO Logo\nLM Studio Dashboard',
            id='logo-title',
            classes='box'
        )
        self.actionlog_widget: ActionLog = ActionLog(
            # TODO: Set relevant values
            name='Action Log',
            id='action-log',
            classes='box'
        )
        self.loadedmodels_widget: LoadedModels = LoadedModels(
            # TODO: Set relevant values
            name='Actively Loaded Models',
            id='loaded-models',
            classes='box'
        )
        self.downloadedmodels_widget: DownloadedModels = DownloadedModels(
            # TODO: Set relevant values
            name='Downloaded Models',
            id='downloaded-models',
            classes='box'
        )
        self.contextpane_widget: ContextPane = ContextPane(
            # TODO: Set relevant values
            name='Dynamic Context Pane',
            id='context-pane',
            classes='box'
        )

        # Top row telemetry and logging
        with Horizontal(id='header-zone'):
            yield self.connection_widget
            yield self.title_widget
            yield self.actionlog_widget

        # Middle row for main application content
        with Horizontal(id='main-zone'):
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
        """Triggered by 's' hotkey"""
        # TODO: Push modal screen to prompt for IP or network scan
        self.notify('Calling change server screen')

    def action_retry_connection(self) -> None:
        self.notify("Retesting connection to server...")
        self.connection_widget.update_connection_status()
