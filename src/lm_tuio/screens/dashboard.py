"""Primary application interface and management screen.

Container for interactive and display components.
"""

from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Input, Label, ProgressBar

from lm_tuio import api, components as comp, events, models as mdl, screens
from lm_tuio.config import KeymapManager

DL_CHECK_INTVL: float = 2.0
MAX_NUM_DL_STATUS_ERROR = 5


class DashboardScreen(Screen):
    """Primary application dashboard."""

    AUTO_FOCUS = "#downloaded_models"

    BINDINGS = KeymapManager.get_bindings("global")

    filter_str: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        # Set widget instances
        self.connection_widget: comp.ConnectionStatus = comp.ConnectionStatus(
            "Connection Status", id="conn-status", classes="box"
        )
        self.connection_widget.border_title = self.connection_widget.name

        self.title_widget: comp.Title = comp.Title(
            name="LM Studio Dashboard", id="logo-title", classes="box"
        )
        self.title_widget.border_subtitle = self.title_widget.name

        self.actionlog_widget: comp.ActionLog = comp.ActionLog(
            name="Actions / Logs",
            id="action-log",
            classes="box",
        )
        self.actionlog_widget.border_title = self.actionlog_widget.name

        self.loadedmodels_widget: comp.LoadedModels = comp.LoadedModels(
            post_unload_model_request_callback=events.UnloadInstancesRequested,
            post_highlighted_model_callback=events.ModelSelected,
            name="Actively Loaded Models",
            id="loaded-models",
            classes="box",
        )
        self.loadedmodels_widget.border_title = self.loadedmodels_widget.name

        self.downloadedmodels_widget: mdl.DownloadedModels = mdl.DownloadedModels(
            post_highlighted_model_callback=events.ModelSelected,
            post_model_load_callback=events.ModelLoadRequest,
            post_action_logger_update_callback=events.ActionLogUpdate,
            name="Downloaded Models",
            id="downloaded-models",
            classes="box",
        )
        self.downloadedmodels_widget.border_title = self.downloadedmodels_widget.name

        self.contextpane_widget: comp.ContextPane = comp.ContextPane(
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

        self.dl_progress_bar: ProgressBar = ProgressBar(
            total=100, show_eta=True, id="download-progress-bar", classes="hidden"
        )

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
            with HorizontalGroup():
                yield self.filter_label
                yield self.filter_label_val
            yield self.dl_progress_bar

        yield self.main_footer
        yield self.search_bar

    def clear_fetched_data(self) -> None:
        """Clears all data dependent on connected server"""
        self.downloadedmodels_widget.clear_model_list()
        self.downloadedmodels_widget.refresh_table()
        self.loadedmodels_widget.clear_model_list()
        self.loadedmodels_widget.refresh_groups()
        self.contextpane_widget.update_model_context(None)

    def load_model_modal(self, model: mdl.ModelInfo) -> None:
        """Spawn Load Model modal and send API request to LMS endpoint."""

        def _on_dismiss(payload: dict[str, Any] | None) -> None:
            if payload is not None:
                self._api_load_request(model, payload)

        self.app.push_screen(screens.LoadModelModal(model), callback=_on_dismiss)

    def _get_horizontal_panes(self) -> list:
        """Returns the ordered list of primary focusable widgets from left to right."""
        panes = []

        try:
            sel_list = self.loadedmodels_widget.query_one("SelectionList")
            panes.append(sel_list)
        except Exception:
            panes.append(self.loadedmodels_widget.loaded_models_scroll)

        panes.append(self.downloadedmodels_widget.table)
        panes.append(self.contextpane_widget.ctx_insts_table)

        return panes

    @work(exclusive=True)
    async def fetch_load_models(self, ip: str, port: int) -> None:
        """Fetch models from LMS API endpoint and populate UI"""
        self.downloadedmodels_widget.clear_model_list()
        self.downloadedmodels_widget.refresh_table()

        key: str = self.connection_widget.api_key
        models, err = await api.fetch_available_models(ip, port, api_key=key)

        if err:
            self.actionlog_widget.add_entry(f"Failed to fetch models: {err}", "error")
            return

        if models is None:
            self.actionlog_widget.add_entry(f"Found 0 downloaded models at {ip}:{port}")
            return

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

        self.loadedmodels_widget.loading = True
        ip: str = self.connection_widget.server_ip
        port: int = self.connection_widget.server_port
        key: str = self.connection_widget.api_key
        success, err = await api.unload_model_instances(
            ip, port, instance_ids, api_key=key
        )
        self.loadedmodels_widget.loading = False

        if not success:
            self.actionlog_widget.add_entry(f"Unload error: {err}", "error")
        else:
            self.actionlog_widget.add_entry(
                f"Successfully unloaded {count} model instance{'s' if count > 1 else ''}",
                "ok",
            )

        self.action_refresh_models()

    @work(exclusive=True)
    async def _api_load_request(
        self, model: mdl.ModelInfo, payload: dict[str, Any] | None
    ):
        if payload is None:
            return

        self.loadedmodels_widget.loading = True
        ip: str = self.connection_widget.server_ip
        port: int = self.connection_widget.server_port
        key: str = self.connection_widget.api_key
        success, err = await api.load_model_instance(ip, port, payload, api_key=key)
        self.loadedmodels_widget.loading = False

        if not success:
            self.actionlog_widget.add_entry(f"Load error: {err}", "error")
        else:
            self.actionlog_widget.add_entry(
                f"Successfully loaded {model} instance",
                "ok",
            )

        self.action_refresh_models()

    async def _get_dl_progress(
        self, ip: str, port: int, key: str, job_id: str, target: str
    ) -> None:
        """Polls API endpoint for model download status updates."""

        import asyncio

        is_downloading: bool = True
        error_count: int = 0
        while is_downloading:
            await asyncio.sleep(DL_CHECK_INTVL)

            status_data, poll_err = await api.check_download_progress(
                ip, port, job_id, api_key=key
            )

            if poll_err or not status_data:
                self.actionlog_widget.add_entry(
                    f"Error checking status: {poll_err}", "warn"
                )
                error_count += 1
                if error_count >= MAX_NUM_DL_STATUS_ERROR:
                    break
                else:
                    continue

            status = status_data.get("status")
            dl_bytes = status_data.get("downloaded_bytes", 0)
            total_bytes = status_data.get("total_size_bytes", 0)

            # Calculate percentage
            if total_bytes > 0:
                pct = (dl_bytes / total_bytes) * 100
                self.dl_progress_bar.progress = pct

            # Check termination states
            if status == "completed":
                self.actionlog_widget.add_entry(
                    f"Successfully downloaded {target}", "ok"
                )
                is_downloading = False
                break
            elif status == "failed":
                self.actionlog_widget.add_entry(f"Download failed for {target}", "err")
                is_downloading = False
                break
            elif status == "downloading" or status == "paused":
                is_downloading = True
                continue
            else:
                self.actionlog_widget.add_entry(
                    f"Unknown download status for {target}. Check server for details",
                    "err",
                )
                is_downloading = True
                break

    @work(exclusive=True)
    async def manage_model_download(self, target: str) -> None:
        """Triggers model download and polls status to update Dashboard progress bar."""
        ip: str = self.connection_widget.server_ip
        port: int = self.connection_widget.server_port
        key: str = self.connection_widget.api_key

        self.actionlog_widget.add_entry(f"Starting download for {target}...", "info")

        job_id, initial_status, err = await api.start_download(
            ip, port, target, api_key=key
        )

        if err:
            self.actionlog_widget.add_entry(f"Download failed to start: {err}", "error")
            return

        # Check for existing download / download in progress
        if initial_status == "already_downloaded":
            self.actionlog_widget.add_entry(
                f"Model {target} is already downloaded.", "success"
            )
            self.action_refresh_models()
            return
        elif initial_status == "downloading":
            self.actionlog_widget.add_entry(
                f"Download still in progress. Aborting new download", "warn"
            )
            # TODO: Implement progress bar latch-on to current download process
            return

        if not job_id:
            self.actionlog_widget.add_entry(
                "Failed to retrieve download job_id from server.", "error"
            )
            return

        self.dl_progress_bar.remove_class("hidden")
        self.dl_progress_bar.progress = 0.0

        await self._get_dl_progress(ip, port, key, job_id, target)

        self.dl_progress_bar.add_class("hidden")
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

    def action_focus_left(self) -> None:
        """Move focus one pane to the left (ctrl+h / ctrl+left)."""
        panes = self._get_horizontal_panes()
        focused = self.app.focused

        # Find current focus
        current_idx = -1
        for idx, pane in enumerate(panes):
            if pane == focused or pane.has_focus_within:
                current_idx = idx
                break

        if current_idx >= 0:
            panes[(current_idx - 1) % 3].focus()
        elif current_idx == -1:
            self.downloadedmodels_widget.table.focus()  # Default middle table

    def action_focus_right(self) -> None:
        """Move focus one pane to the right (ctrl+l / ctrl+right)."""
        panes = self._get_horizontal_panes()
        focused = self.app.focused

        current_idx = -1
        for idx, pane in enumerate(panes):
            if pane == focused or pane.has_focus_within:
                current_idx = idx
                break

        if 0 <= current_idx <= len(panes) - 1:
            panes[(current_idx + 1) % 3].focus()
        elif current_idx == -1:
            self.downloadedmodels_widget.table.focus()

    def action_focus_up(self) -> None:
        """Jump focus up to the header ActionLog (ctrl+k / ctrl+up)."""
        self.actionlog_widget.focus()

    def action_focus_down(self) -> None:
        """Jump focus down from the header back to the main models table (ctrl+j / ctrl+down)."""
        self.downloadedmodels_widget.table.focus()

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
            result: tuple[str, int, str, list[tuple[str, str]]]
            | tuple[None, list[tuple[str, str]]],
        ) -> None:
            """Returns result of Server Selection modal and rebuilds logs to ActionLog.

            result = (IP, Port, API Key, Logs) | (None, Logs)
            """

            if result[0] is None and isinstance(result[1], list):
                for log in result[1]:
                    # log[0] = msg, log[1] = severity
                    self.post_message(events.ActionLogUpdate(log[0], log[1]))
                return

            assert (
                len(result) == 4
                and isinstance(result[0], str)
                and isinstance(result[1], int)
                and isinstance(result[2], str)
                and isinstance(result[3], list)
            )

            ip, port, api_key, logs = result
            if ip and port:
                self.connection_widget.api_key = api_key
                self.connection_widget.apply_new_server((ip, port))
                self.post_message(events.ServerEndpointUpdated(ip, port))

            for log in logs:
                self.post_message(events.ActionLogUpdate(log[0], log[1]))

        self.app.push_screen(screens.ServerSelectionModal(), callback=is_same_server)

    def action_refresh_models(self) -> None:
        self.actionlog_widget.add_entry("Refreshing model lists...", "info")
        self.fetch_load_models(
            self.connection_widget.server_ip,
            self.connection_widget.server_port,
        )

    def action_test_connection(self) -> None:
        """Default hotkey '*' to retest connection to API endpoint"""
        self.actionlog_widget.add_entry("Retesting connection to server...", "info")
        self.connection_widget.reset_status()
        self.connection_widget.update_connection_status()

    def action_show_keybinds(self) -> None:
        """Open keybinds help screen."""
        self.app.push_screen(screens.KeybindsModal())

    def action_unload_all(self) -> None:
        self.loadedmodels_widget.action_unload_all()

    def action_show_action_log(self) -> None:
        """Spawn full viewer Action Log."""
        log_history = self.actionlog_widget.history
        self.app.push_screen(screens.ActionLogModal(history=log_history))

    def action_download_model(self) -> None:
        """Spawn Download Model modal."""

        def _on_model_submit(target: str | None) -> None:
            if target is not None:
                self.manage_model_download(target)

        self.app.push_screen(screens.DownloadModelModal(), callback=_on_model_submit)

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

    @on(events.ModelLoadRequest)
    def handle_load_model(self, event: events.ModelLoadRequest) -> None:
        if event.model:
            self.load_model_modal(event.model)

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
