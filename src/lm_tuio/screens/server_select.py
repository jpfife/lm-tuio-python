"""Secondary pop-up modal used to connect to specified LMS API server.

Spawned from primary dashboard on launch (if no CLI IP supplied), or manual launch via hotkey.
Displays current listing of active servers on network and cached IPs.
Pulls defaults from config.toml.
"""

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalScroll, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, OptionList

from lm_tuio.config import validate_ip_net, AppConfig
from lm_tuio.scanner import scan_targets


class ServerSelectionModal(ModalScreen[tuple[str, int] | None]):
    """Modal to select, scan, and set active LMS API endpoints."""

    BINDINGS = [
        ("q,escape", "quit", "[quit]"),
    ]

    def __init__(self, current_ip: str, current_port: int, default_subnet: str) -> None:
        super().__init__()
        self.current_ip: str = current_ip
        self.current_port: int = current_port
        self.default_subnet: str = default_subnet

    def compose(self) -> ComposeResult:
        self.input_widget: Input = Input(
            value=f"{self.current_ip.split('/', 1)[0]}:{self.current_port}",
            placeholder="IP|hostname:[Port], default LMS port:1234",
            id="manual-ip-input",
            classes="server-select-input-field",
        )
        self.scan_widget: Input = Input(
            value=self.default_subnet,
            placeholder="Subnet (e.g., 192.168.1.0/24)",
            id="scan-input",
            classes="server-select-input-field",
        )
        self.scan_port_widget: Input = Input(
            value=str(self.current_port),
            placeholder="Port (e.g., 1234)",
            id="scan-port-input",
            classes="server-select-input-field",
        )
        self.input_widget.border_subtitle = "Server IP"
        self.scan_widget.border_subtitle = "Subnet"
        self.scan_port_widget.border_subtitle = "Port"

        with Horizontal(id="modal-container"):
            # Left sidebar
            with Vertical(id="sidebar"):
                yield Label("Active Servers", classes="section-title")
                with VerticalScroll(id="active-server-sidebar"):
                    yield OptionList(
                        "192.168.1.100:1234",
                        "10.0.0.5:8080",
                        id="active-servers-list",
                    )  # TODO: Populate vals from active scan
                yield Label("Cached IPs", classes="section-title")
                with VerticalScroll(id="cached-ips-sidebar"):
                    yield OptionList("127.0.0.1:1234", id="cached-ips-list")

            # Right main area
            with Vertical(id="main-action-area"):
                with Vertical(id="server-section"):
                    yield Label("Connect to Server", classes="section-title")
                    yield self.input_widget
                    with Horizontal(classes="input-group"):
                        yield Button("Connect", id="connect-btn", variant="primary")
                        yield Button(
                            "Set Default", id="default-connect-btn", variant="primary"
                        )

                with Vertical(id="scan-section"):
                    yield Label("Scan for Servers", classes="section-title")
                    yield self.scan_widget
                    yield self.scan_port_widget
                    with Horizontal(classes="input-group"):
                        yield Button("Scan", id="scan-btn", variant="primary")
                        yield Button(
                            "Set Default", id="default-network-btn", variant="primary"
                        )

                with Vertical(id="bottom-btn-group", classes="button-group"):
                    yield Button("Cancel (q)", id="cancel-btn", variant="error")

    def on_mount(self) -> None:
        self.exectute_network_scan(self.default_subnet, self.current_port)

    @work(exclusive=True)
    async def exectute_network_scan(
        self, target_network: str, target_port: int | str
    ) -> None:
        """Async network scan. Updates Active Servers list on SelectServer modal."""
        active_list: OptionList = self.query_one("#active-servers-list", OptionList)
        active_list.clear_options()
        valid_net, err = validate_ip_net(target_network)

        if err is not None:
            self.notify(
                f"Scan failed: {err}",
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            active_list.add_option("Invalid network format.")
            active_list.disabled = True
            return

        try:
            port_num: int = int(target_port)
            assert 1 <= port_num <= 65535
        except ValueError as err:
            self.notify(
                "Scan port must be a number between 1 - 65535",
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            # TODO: Send err to logger display
            return
        except AssertionError as err:
            self.notify(
                "Invalid port number. Must be between 1 - 65535",
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            # TODO: Send err to logger display
            return

        self.notify(
            f"Scanning network {valid_net}...", timeout=AppConfig.NOTIFY_TIMEOUT
        )
        active_list.add_option("Scanning...")
        active_list.disabled = True

        assert isinstance(valid_net, str)
        scan_config: AppConfig = AppConfig(
            target=target_network,
            port=port_num,
            scan_subnet=valid_net,
            is_network=True,
        )

        hosts, scan_err = await scan_targets(scan_config)
        active_list.clear_options()

        if scan_err:
            self.notify(scan_err, severity="warning", timeout=AppConfig.NOTIFY_TIMEOUT)
            active_list.add_option("No servers found.")
        elif hosts:
            self.notify(
                f"Found {len(hosts)} active server(s).",
                severity="information",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            options = [f"{host}:{self.current_port}" for host in hosts]
            active_list.add_options(options)
            active_list.disabled = False
        else:
            self.notify(
                "Found 0 server endpoints on network.", timeout=AppConfig.NOTIFY_TIMEOUT
            )

    # ========== BUTTON HANDLERS ==========

    @on(Button.Pressed, "#connect-btn")
    def connect_to_new_server(self) -> None:
        """Parses and validates manual input, emits update event."""
        target = self.input_widget.value.strip()

        try:
            if ":" in target:
                ip, port_str = target.split(":", 1)
                port = int(port_str)
                assert 1 <= port <= 65535
            else:
                ip = target
                port = 1234

            valid_ip, err = validate_ip_net(ip)
            if err is not None:
                self.notify(
                    "Invalid network target.\nExpected: IP:Port (e.g., 192.168.1.10:1234)",
                    severity="error",
                )
                return

            assert valid_ip is not None
            ip = ip[: ip.find("/")] if "/" in ip else ip
            self.dismiss((ip, port))

        except (ValueError, AssertionError):
            self.notify(
                """Invalid network target.
                Use format IP:Port or hostname:Port""",
                severity="error",
            )

    @on(Button.Pressed, "#cancel-btn")
    def cancel_modal(self) -> None:
        """Closes the modal without making changes."""
        self.dismiss()

    @on(Button.Pressed, "#scan-btn")
    def run_network_scan(self) -> None:
        """Placeholder for scanner integration."""
        target_net = self.scan_widget.value
        target_port = self.scan_port_widget.value
        self.exectute_network_scan(target_net, target_port)

    @on(OptionList.OptionSelected, "#active-servers-list")
    def select_scanned_server(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.disabled:
            return
        selected_endpoint: str = str(event.option.prompt)
        self.input_widget.value = selected_endpoint

    @on(Button.Pressed, "#set-default-net-btn")
    def update_default_network(self) -> None:
        """Placeholder for TOML configuration writing."""
        target_net = self.scan_widget.value
        self.notify(f"Default network set to {target_net}")
        # TODO: Wire to config writer

    # ======= ACTIONS =======

    def action_quit(self) -> None:
        """Triggered by 'q' hotkey"""
        self.dismiss()
