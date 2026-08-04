"""Primary application interface and management screen.

Container for interactive and display components.
"""

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Input, Label, SelectionList

from lm_tuio import api, events, models as md
from lm_tuio.components import ActionLog, ConnectionStatus, ContextPane, Title
from lm_tuio.components.loaded_models import LoadedModels
from lm_tuio.screens.server_select import ServerSelectionModal


class DashboardScreen(Screen):
    """Primary application dashboard."""

    AUTO_FOCUS = "#downloaded_models"

    BINDINGS = [
        ("q", "quit", "<quit>"),
        ("c", "change_server", "<change server>"),
        ("r", "refresh_models", "<refresh models>"),
        ("/", "filter", "<filter>"),
        ("escape,ctrl+left_square_bracket", "clear_filter", "<clr filter>"),
        ("*", "retry_connection"),
        ("u", "unload_selected", "<unload selected>"),
        ("U", "unload_all", "<unload all>"),
    ]

    filter_str: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        # Set widget instances
        self.connection_widget: ConnectionStatus = ConnectionStatus(
            "Connection Status", id="conn-status", classes="box"
        )
        self.connection_widget.border_title = self.connection_widget.name

        self.title_widget: Title = Title(
            name="LM Studio Dashboard", id="logo-title", classes="box"
        )
        self.title_widget.border_subtitle = self.title_widget.name

        self.actionlog_widget: ActionLog = ActionLog(
            name="Actions / Logs",
            id="action-log",
            classes="box",
        )
        self.actionlog_widget.border_title = self.actionlog_widget.name

        self.loadedmodels_widget: LoadedModels = LoadedModels(
            post_unload_model_request_callback=events.UnloadInstancesRequested,
            post_highlighted_model_callback=events.ModelSelected,
            name="Actively Loaded Models",
            id="loaded-models",
            classes="box",
        )
        self.loadedmodels_widget.border_title = self.loadedmodels_widget.name

        self.downloadedmodels_widget: md.DownloadedModels = md.DownloadedModels(
            post_highlighted_model_callback=events.ModelSelected,
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
            placeholder="Set list filter, ESC to cancel",
            name="Filter",
            id="search-bar",
            classes="footers hidden",
        )
        self.search_bar.border_title = self.search_bar.name

        # Filter 'toggle'
        self.filter_label: Label = Label("Filter: ", id="filter-label")
        self.filter_label_val: Label = Label("OFF", id="filter-label-val")
        self.filter_label_val.styles.text_style = "bold"
        self.filter_label_val.styles.background = self.app.theme_variables["surface"]

        self.main_footer: Footer = Footer(id="main-footer", classes="footers")

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
        with Horizontal(id="filter-label-zone"):
            yield self.filter_label
            yield self.filter_label_val

        yield self.main_footer
        yield self.search_bar

    def clear_fetched_data(self) -> None:
        """Clears all data dependent on connected server"""
        self.downloadedmodels_widget.clear_model_list()
        self.downloadedmodels_widget.refresh_table()
        self.loadedmodels_widget.clear_model_list()
        self.loadedmodels_widget.refresh_groups()
        self.contextpane_widget.update_model_context(None)

    @work(exclusive=True)
    async def fetch_load_models(self, ip: str, port: int) -> None:
        """Fetch models from LMS API endpoint and populate UI"""
        self.downloadedmodels_widget.clear_model_list()
        self.downloadedmodels_widget.refresh_table()
        models, err = await api.fetch_available_models(ip, port)

        if err:
            self.actionlog_widget.add_entry(f"Failed to fetch models: {err}", "error")
            return

        assert models
        self.downloadedmodels_widget.load_models(models)
        self.downloadedmodels_widget.table.focus()
        self.actionlog_widget.add_entry(
            f"Found {len(models)} downloaded models at {ip}:{port}"
        )

        self.loadedmodels_widget.load_model_groups(models)

    @work(exclusive=True)
    async def unload_models(self, instance_ids: list[str]) -> None:
        """Execute API unload requests and refresh dashboard."""
        count = len(instance_ids)
        self.actionlog_widget.add_entry(
            f"Unloading {count} model instance{'s' if count > 1 else ''}..."
        )

        success, err = await api.unload_model_instances(
            self.connection_widget.server_ip,
            self.connection_widget.server_port,
            instance_ids,
        )

        if not success:
            self.actionlog_widget.add_entry(f"Unload error: {err}", "error")
        else:
            self.actionlog_widget.add_entry(
                f"Successfully unloaded {count} model instance{'s' if count > 1 else ''}",
                "ok",
            )

        self.action_refresh_models()

    # ======= REACTIVE WATCHERS =======
    def watch_filter_str(self, new_filter: str) -> None:
        self.downloadedmodels_widget.apply_filter(new_filter)
        self.loadedmodels_widget.apply_filter(new_filter)

        if self.filter_str:
            self.filter_label_val.update(" ON ")
            self.filter_label_val.styles.background = self.app.theme_variables[
                "primary"
            ]
            self.filter_label_val.styles.color = self.app.theme_variables["background"]
        else:
            self.filter_label_val.update(" OFF ")
            self.filter_label_val.styles.background = self.app.theme_variables[
                "surface"
            ]
            self.filter_label_val.styles.color = self.app.theme_variables["foreground"]

    # ========== ACTIONS ==========

    def action_filter(self) -> None:
        """Default hotkey '/' to filter display lists"""
        self.main_footer.display = False
        self.search_bar.display = True
        self.search_bar.value = self.filter_str
        self.search_bar.focus()

    def action_clear_filter(self) -> None:
        """Default hotkey 'Esc' to clear filter"""
        self.filter_str = ""
        self._hide_search_bar()

    def action_quit(self) -> None:
        """Default hotkey 'q' to quit application"""
        self.app.exit()

    def action_change_server(self) -> None:
        """Default hotkey 'c' to connect to server"""

        # Track if endpoint actually changes
        def is_same_server(
            result: tuple[str, int, list[tuple[str, str]]]
            | tuple[None, list[tuple[str, str]]],
        ) -> None:
            """Returns result of Server Selection modal and rebuilds logs to ActionLog.

            result = (IP, Port, Logs) | (None, Logs)
            """

            if result[0] is None and isinstance(result[1], list):
                for log in result[1]:
                    self.post_message(events.ActionLogUpdate(log[0], log[1]))
                return

            assert (
                len(result) == 3
                and isinstance(result[0], str)
                and isinstance(result[1], int)
                and isinstance(result[2], list)
            )

            ip, port, logs = result
            if ip and port:
                self.connection_widget.apply_new_server((ip, port))
                self.post_message(events.ServerEndpointUpdated(ip, port))

            for log in logs:
                self.post_message(events.ActionLogUpdate(log[0], log[1]))

        self.app.push_screen(ServerSelectionModal(), callback=is_same_server)

    def action_refresh_models(self) -> None:
        self.fetch_load_models(
            self.connection_widget.server_ip, self.connection_widget.server_port
        )

    def action_retry_connection(self) -> None:
        """Default hotkey '*' to retest connection to API endpoint"""
        self.actionlog_widget.add_entry("Retesting connection to server...")
        self.connection_widget.reset_status()
        self.connection_widget.update_connection_status()

    def action_unload_selected(self) -> None:
        """Gathers all checkboxes across all collapsible groups and fires unload."""
        selected_ids: list[str] = []
        for sel_list in self.query(SelectionList):
            selected_ids.extend(sel_list.selected)

        if selected_ids:
            # self.post_message(
            #     self.loadedmodels_widget.post_unload_model_request(selected_ids)
            # )
            self.unload_models(selected_ids)
        else:
            self.actionlog_widget.add_entry(
                "No instances checked for unloading", "warn"
            )

    def action_unload_all(self) -> None:
        """Sends all currently loaded model instances for unload."""
        all_ids = list(self.loadedmodels_widget._instance_map.keys())
        if all_ids:
            # self.post_message(
            #     self.loadedmodels_widget.post_unload_model_request(all_ids)
            # )
            self.unload_models(all_ids)

    # ========= EVENTS ==========

    @on(events.UnloadInstancesRequested)
    def handle_unload_request(self, event: events.UnloadInstancesRequested) -> None:
        """Listen for unload requests and dispatch async worker."""
        if event.instance_ids:
            self.unload_models(event.instance_ids)

    @on(events.ServerConnected)
    def handle_server_connected(self, event: events.ServerConnected) -> None:
        """Trigger fetch models on successful server connection"""
        self.fetch_load_models(event.ip, event.port)

    @on(events.ServerEndpointUpdated)
    def handle_server_changed(self) -> None:
        """Clears models when server changes, only fetch models on successful connection"""
        self.clear_fetched_data()

    @on(events.ModelSelected)
    def update_context_display(self, event: events.ModelSelected) -> None:
        self.contextpane_widget.update_model_context(event.model)

    @on(Input.Submitted, "#search-bar")
    def apply_search(self) -> None:
        """Filters active widget DataTable"""
        self._hide_search_bar()
        self.downloadedmodels_widget.table.focus()

    @on(Input.Changed, "#search-bar")
    def real_time_search(self, event: Input.Changed) -> None:
        """Real-time text filtering"""
        self.filter_str = event.value

    @on(events.ActionLogUpdate)
    def update_action_log(self, event: events.ActionLogUpdate) -> None:
        """Passes fired messages to ActionLog."""
        msg: str = event.msg
        sev: str = event.severity
        self.actionlog_widget.add_entry(msg, sev)

    def on_key(self, event) -> None:
        """Esc key listener for filter search"""
        if self.search_bar.display and (
            event.key == "escape" or event.key == "ctrl+left_square_bracket"
        ):
            self._hide_search_bar()
            self.downloadedmodels_widget.table.focus()

    def _hide_search_bar(self) -> None:
        """Helper to swap main footer back"""
        self.search_bar.display = False
        self.main_footer.display = True
