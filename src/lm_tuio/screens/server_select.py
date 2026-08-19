"""Secondary pop-up modal used to connect to specified LMS API server.

Spawned from primary dashboard on launch (if no CLI IP supplied), or manual launch via hotkey.
Displays current listing of active servers on network and cached IPs.
Pulls defaults from config.toml.
"""

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label, OptionList

from lm_tuio.config import keymap, secrets
from lm_tuio.config.settings import AppConfig, validate_ip_net
from lm_tuio.events import ServerEndpointUpdated
from lm_tuio.scanner import scan_targets


class ServerSelectionModal(
    ModalScreen[
        tuple[str, int, str, list[tuple[str, str]]] | tuple[None, list[tuple[str, str]]]
    ]
):
    """Modal to select, scan, and set active LMS API endpoints.

    Returns tuple(IP, Port, and logs, if any were generated.
    If modal is closed without setting new endpoints, None is passed with any logs
    to update ActionLog on the Dashboard.
    """

    BINDINGS = keymap.KeymapManager.get_bindings("server_select")

    current_ip: str
    current_port: int
    default_subnet: str

    logs: list[tuple[str, str]]

    def __init__(
        self, ip: str = "", port: int = 0, subnet: str = "", *args, **kwargs
    ) -> None:
        self.logs = []

        # Don't load config if all args are passed in
        if ip and port and subnet:
            self.current_ip = ip
            self.current_port = port
            self.default_subnet = subnet
            super().__init__(*args, **kwargs)
            return

        app_config: AppConfig | None = getattr(self.app, "config", None)
        # Load config from config.toml if found, otherwise default AppConfig
        if not app_config:
            loaded_config, config_err = AppConfig().load()
            if config_err:
                self.notify(
                    config_err, severity="warning", timeout=AppConfig.NOTIFY_TIMEOUT
                )
                self.logs.append((config_err, "warn"))
            else:
                err_msg: str = "Error: Could not resolve configuration"
                self.notify(
                    err_msg,
                    severity="warning",
                    timeout=AppConfig.NOTIFY_TIMEOUT,
                )
                self.logs.append((err_msg, "warn"))

        else:
            loaded_config, config_err = app_config.load()

        # Override defaults if args are passed
        assert isinstance(loaded_config, AppConfig)
        self.current_ip = ip if ip else loaded_config.target
        self.current_port = port if port else loaded_config.port
        self.default_subnet = subnet if subnet else loaded_config.scan_subnet

        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        self.input_widget: Input = Input(
            value=f"{self.current_ip}:{self.current_port}",
            placeholder="IP:[Port]",
            id="manual-ip-input",
            classes="input-field",
        )
        self.api_key_widget: Input = Input(
            placeholder="API Key (Optional)",
            password=True,
            id="api-key-input",
            classes="input-field",
        )
        self.scan_widget: Input = Input(
            value=self.default_subnet,
            placeholder="Subnet (e.g., 192.168.1.0/24)",
            id="scan-input",
            classes="input-field",
        )
        self.scan_port_widget: Input = Input(
            value=str(self.current_port),
            placeholder="Port (e.g., 1234)",
            id="scan-port-input",
            classes="input-field",
        )
        self.input_widget.border_subtitle = "Server IP"
        self.api_key_widget.border_subtitle = "API Key"
        self.scan_widget.border_subtitle = "Subnet"
        self.scan_port_widget.border_subtitle = "Port"

        with Horizontal(id="modal-container"):
            # Left sidebar
            with Vertical(id="sidebar"):
                yield Label("Active Servers", classes="section-title")
                yield OptionList(id="active-servers-list")
                yield Label("Cached IPs", classes="section-title")
                yield OptionList(id="cached-ips-list")
                yield Button("Clear Cache", id="clear-cache-btn", variant="warning")

            # Right main area
            with Vertical(id="main-action-area"):
                with Vertical(id="server-section"):
                    yield Label("Connect to Server", classes="section-title")
                    yield self.input_widget
                    yield self.api_key_widget
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
                    yield Button("Cancel", id="cancel-btn", variant="error")

            yield Footer()

    def on_mount(self) -> None:
        """Populate cached IPs and conduct default network scan."""

        self.cache_list: OptionList = self.query_one("#cached-ips-list", OptionList)
        self.active_ips: OptionList = self.query_one("#active-servers-list", OptionList)

        app_config = getattr(self.app, "config", None)
        if isinstance(app_config, AppConfig) and app_config.cached_ips:
            self.cache_list.add_options(app_config.cached_ips)

        self.api_key_widget.value = secrets.SecretsManager.get_api_key(
            self.current_ip, self.current_port
        )
        self.exectute_network_scan(self.default_subnet, self.current_port)

    @work(exclusive=True)
    async def exectute_network_scan(
        self, target_network: str, target_port: int | str
    ) -> None:
        """Async network scan. Updates Active Servers list on SelectServer modal.

        Args: target_network: str, target_port: int | str
        """
        active_list = self.active_ips
        active_list.clear_options()
        valid_net, err = validate_ip_net(target_network)

        if err is not None:
            err_str: str = f"Scan failed: {err}"
            self.notify(
                err_str,
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            self.logs.append((err_str, "err"))
            active_list.add_option("Invalid network format.")
            active_list.disabled = True
            return

        try:
            port_num: int = int(target_port)
            assert 1 <= port_num <= 65535
        except ValueError as err:
            self.notify(
                "Scan port must be a number between 1-65535",
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            return
        except AssertionError as _err:
            self.notify(
                "Invalid port number. Must be between 1-65535",
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            return

        self.logs.append((f"Scanned {valid_net}", "info"))
        active_list.add_option("Scanning...")
        active_list.disabled = True

        assert isinstance(valid_net, str)
        scan_config: AppConfig = AppConfig(
            target=target_network,
            port=port_num,
            scan_subnet=valid_net,
            is_network=True,
        )
        self.current_port = scan_config.port

        servers, scan_err = await scan_targets(scan_config)
        active_list.clear_options()

        if scan_err:
            self.notify(scan_err, severity="warning", timeout=AppConfig.NOTIFY_TIMEOUT)
            self.logs.append((scan_err, "warn"))
            active_list.add_option("No servers found.")
        elif servers:
            success_msg: str = f"Found {len(servers)} active server(s)"
            self.logs.append((success_msg, "ok"))
            options = [f"{server}:{self.current_port}" for server in servers]
            active_list.add_options(options)
            active_list.disabled = False
        else:
            err_msg: str = f"Found 0 server endpoints on {valid_net} network"
            self.notify(err_msg, timeout=AppConfig.NOTIFY_TIMEOUT)
            self.logs.append((err_msg, "err"))

    @staticmethod
    def _validate_connection_input(
        raw_input: str, is_subnet: bool = False
    ) -> tuple[str, int, str] | tuple[None, None, str]:
        """Parses raw connection field input and returns tuple IP[str], Port[int] and response, or error."""
        ip: str
        port_str: str

        if ":" in raw_input:
            ip, port_str = raw_input.strip().split(":", 1)
            try:
                port = int(port_str)
                assert 1 <= port <= 65535
            except ValueError:
                return None, None, "Invalid port: Port must be a number"
            except AssertionError:
                return None, None, "Invalid port: Port must be between 1-65535"
        else:
            ip = raw_input.strip()
            port = AppConfig.port

        try:
            valid_ip, err = validate_ip_net(ip)
            if (err is not None) and is_subnet:
                return (
                    None,
                    None,
                    f"Invalid network scan config: {valid_ip}, {port}\nExpected: IP/[CIDR] and valid port.",
                )
            elif (err is not None) and not is_subnet:
                return (
                    None,
                    None,
                    f"Invalid network target {ip}:{port}.\nExpected: IP:Port (e.g., 192.168.1.10:1234)",
                )

            assert valid_ip is not None
            if is_subnet:
                return (
                    valid_ip,
                    port,
                    f"Valid network config: {valid_ip} scan on port {port}",
                )
            ip = ip[: ip.find("/")] if "/" in ip else ip
            return ip, port, f"Valid address: {ip}:{port}"

        except (AssertionError, ValueError):
            return (
                None,
                None,
                f"Invalid network target {ip}:{port}.\nExpected: IP:Port (e.g., 192.168.1.10:1234)",
            )

    # ========== BUTTON HANDLERS ==========

    @on(OptionList.OptionSelected, "#cached-ips-list")
    @on(OptionList.OptionSelected, "#active-servers-list")
    @on(Input.Submitted, "#manual-ip-input")
    @on(Input.Submitted, "#api-key-input")
    @on(Button.Pressed, "#connect-btn")
    def connect_to_new_server(self) -> None:
        """Parses and validates manual input; updates IP cache on submission."""

        target: str = self.input_widget.value.strip()
        api_key: str = self.api_key_widget.value.strip()
        ip, port, response = self._validate_connection_input(target, is_subnet=False)
        self.logs.append((response, "info"))

        if (ip and port) is not None:
            assert isinstance(ip, str)
            assert isinstance(port, int)
            secrets.SecretsManager.save_api_key(ip, port, api_key)
            self.post_message(ServerEndpointUpdated(ip, port))

            endpoint_str: str = f"{ip}:{port}"

            app_config = getattr(self.app, "config", None)
            if isinstance(app_config, AppConfig):
                if endpoint_str in app_config.cached_ips:
                    self.dismiss((ip, port, api_key, self.logs))
                    return
                app_config.cached_ips.insert(0, endpoint_str)
                app_config.cached_ips = app_config.cached_ips[
                    : app_config.MAX_CACHED_IPS
                ]
                app_config.save()

            self.dismiss((ip, port, api_key, self.logs))
        else:
            err_msg = "Error validating network enpoint."
            self.notify(
                err_msg,
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            self.logs.append((err_msg, "err"))

    @on(Button.Pressed, "#default-connect-btn")
    def set_default_connection(self) -> None:
        """Saves manual connect target to config.toml"""
        target: str = self.input_widget.value.strip()
        api_key: str = self.api_key_widget.value.strip()
        ip, port, response = self._validate_connection_input(target, is_subnet=False)
        self.logs.append((response, "info"))

        if (ip and port) is not None:
            assert isinstance(ip, str)
            assert isinstance(port, int)
            secrets.SecretsManager.save_api_key(ip, port, api_key)

        else:
            err_msg: str = "Error validating network enpoint."
            self.notify(
                err_msg,
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            self.logs.append((err_msg, "err"))
            return

        app_config: AppConfig | None = getattr(self.app, "config", None)

        if isinstance(app_config, AppConfig):
            app_config.target, app_config.port = ip, port
            save_msg = app_config.save()
            self.notify(
                save_msg,
                severity="information",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            self.logs.append((save_msg, "info"))
        else:
            err_msg: str = "Error: Configuration not found."
            self.notify(
                err_msg,
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            self.logs.append((err_msg, "err"))

    @on(Input.Submitted, "#scan-port-input")
    @on(Input.Submitted, "#scan-input")
    @on(Button.Pressed, "#scan-btn")
    def run_network_scan(self) -> None:
        """Provides list of all servers responding on subnet to HTTP Head request on selected port."""
        target_net = self.scan_widget.value.strip()
        target_port = self.scan_port_widget.value.strip()
        self.exectute_network_scan(target_net, target_port)

    @on(Button.Pressed, "#default-network-btn")
    def set_default_network(self) -> None:
        """Placeholder for TOML configuration writing."""
        target_net: str = self.scan_widget.value.strip()
        target_port: str = self.scan_port_widget.value.strip()
        raw_ip_str: str = f"{target_net}:{target_port}"

        ip_net, port, response = self._validate_connection_input(
            raw_ip_str, is_subnet=True
        )
        self.logs.append((response, "info"))

        if (ip_net and port) is not None:
            assert isinstance(ip_net, str)
            assert isinstance(port, int)

        else:
            err_msg: str = "Error validating network endpoint"
            self.notify(
                err_msg,
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            self.logs.append((err_msg, "err"))
            return

        app_config: AppConfig | None = getattr(self.app, "config", None)

        if isinstance(app_config, AppConfig):
            app_config.scan_subnet, app_config.port = ip_net, port
            save_msg = app_config.save()
            self.notify(
                save_msg,
                severity="information",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            self.logs.append((save_msg, "info"))
        else:
            err_msg: str = "Error: Configuration not found"
            self.notify(
                err_msg,
                severity="error",
                timeout=AppConfig.NOTIFY_TIMEOUT,
            )
            self.logs.append((err_msg, "err"))

        success_msg: str = f"Default network set to {ip_net}"
        self.notify(success_msg)
        self.logs.append((success_msg, "ok"))

    def _get_cached_endpoint(
        self, event: OptionList.OptionHighlighted
    ) -> tuple[str, str]:
        """Return cached endpoint/API key for Server Connection input fields auto-population."""

        # Get server field value
        selected_endpoint: str = str(event.option.prompt)

        # Get API Key field value
        ip, port, _ = self._validate_connection_input(
            selected_endpoint, is_subnet=False
        )
        key: str = ""
        if ip and port:
            key = secrets.SecretsManager.get_api_key(
                ip, port
            )  # Returns empty str if None

        return selected_endpoint, key

    @on(OptionList.OptionHighlighted, "#active-servers-list")
    def select_scanned_server(self, event: OptionList.OptionHighlighted) -> None:
        """Copy currently selected server and API key into Server Connection input fields."""

        if event.option_list.disabled:
            return

        endpoint, key = self._get_cached_endpoint(event)
        self.input_widget.value = endpoint
        self.api_key_widget.value = key

    @on(OptionList.OptionHighlighted, "#cached-ips-list")
    def select_cached_server(self, event: OptionList.OptionHighlighted) -> None:
        """Copy currently selected cached server and API key into Server Connection input fields."""

        if event.option_list.disabled:
            return

        endpoint, key = self._get_cached_endpoint(event)
        self.input_widget.value = endpoint
        self.api_key_widget.value = key

    @on(Button.Pressed, "#clear-cache-btn")
    def clear_ip_cache(self) -> None:
        """Clears IP cache list and updates saved config."""

        app_config = getattr(self.app, "config", None)
        if isinstance(app_config, AppConfig):
            # Preserve default endpoint before clear
            default_endpoint: str = f"{app_config.target}:{app_config.port}"
            purge_endpoints: list[str] = [
                ip for ip in app_config.cached_ips if ip != default_endpoint
            ]

            # Clear endpoints from SECRETS_FILE
            if purge_endpoints:
                secrets.SecretsManager.remove_endpoints(purge_endpoints)

            app_config.cached_ips.clear()
            app_config.save()

            cache_list = self.query_one("#cached-ips-list", OptionList)
            cache_list.clear_options()
            message: str = "Cache and keys cleared - preserved defaults"
            self.notify(message, severity="information")
            self.logs.append((message, "info"))

    @on(Button.Pressed, "#cancel-btn")
    def cancel_modal(self) -> None:
        """Closes the modal without making changes"""
        self.dismiss((None, self.logs))

    # ======= ACTIONS =======

    def action_select_up(self) -> None:
        widget = self.focused
        if widget == self.active_ips or widget == self.cache_list:
            assert isinstance(widget, OptionList)
            widget.action_cursor_up()

    def action_select_down(self) -> None:
        widget = self.focused
        if widget == self.active_ips or widget == self.cache_list:
            assert isinstance(widget, OptionList)
            widget.action_cursor_down()

    def action_connect_input_submit(self) -> None:
        """Default 'c' hotkey"""
        self.connect_to_new_server()

    def action_scan_network(self) -> None:
        """Default 's' hotkey"""
        self.run_network_scan()

    def action_save_defaults(self) -> None:
        """Default 'S' hotkey"""
        self.set_default_connection()
        self.set_default_network()

    def action_clear_cache(self) -> None:
        """Default 'x' hotkey"""
        self.clear_ip_cache()

    def action_quit(self) -> None:
        """Default 'q' hotkey"""
        self.dismiss((None, self.logs))
