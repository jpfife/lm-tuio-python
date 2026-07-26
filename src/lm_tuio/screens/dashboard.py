from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal
from textual.widgets import Static, Footer


class DashboardScreen(Screen):
    '''Primary dashboard.'''
    BINDINGS = [
        ('q', 'quit', '[quit]'),
        ('s', 'change_server', '[change server]'),
    ]

    def compose(self) -> ComposeResult:
        # Top row telemetry and logging
        with Horizontal(id='header-zone'):
            yield Static('Connectivity Status', id='conn-status', classes='box')
            yield Static('LM TUIO Logo\nLM Studio Dashboard', id='logo-title', classes='box')
            yield Static('Current Actions / Log', id='action-log', classes='box')

        # Middle row for main application content
        with Horizontal(id='main-zone'):
            yield Static('Actively Loaded Models', id='loaded-models', classes='box')
            yield Static('Downloaded Models', id='downloaded-models', classes='box')
            yield Static('Dynamic Context Pane', id='context-pane', classes='box')

        # Bottom row hotkeys bar
        yield Footer()


    # ========== ACTIONS ==========

    def action_change_server(self) -> None:
        """Triggered by 's' hotkey"""
        # TODO: Push modal screen to prompt for IP or network scan
        self.notify('Calling change server screen')

    def action_quit(self) -> None:
        """Triggered by 'q' hotkey"""
        self.app.exit()
