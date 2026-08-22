"""UI element to display active connection to selected LMS server API endpoint.

Periodically requests HTTP HEAD response using ../api.py server check function.
"""

from enum import StrEnum

from textual import work
from textual.reactive import reactive
from textual.widgets import Static

from lm_tuio.api import check_server_status
from lm_tuio.config import SecretsManager
from lm_tuio.config.settings import AppConfig
from lm_tuio.events import ActionLogUpdate, ServerConnected


# Connection status indicator enums
class Connection(StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    GRAY = "gray"


# Easy set connection status icon color (W3C, hex, etc.)
GREEN_ICON: str = "mediumseagreen"
YELLOW_ICON: str = "yellow"
RED_ICON: str = "tomato"
GRAY_ICON: str = "lightgray"


CONNECT_STATUS: dict[str, str] = {
    Connection.GREEN: (f"[{GREEN_ICON}]●[/{GREEN_ICON}]  [i]Connected"),
    Connection.YELLOW: (f"[{YELLOW_ICON}]●[/{YELLOW_ICON}]  [i]Checking endpoint..."),
    Connection.RED: (f"[{RED_ICON}]●[/{RED_ICON}]  [i]No response. Retrying..."),
    Connection.GRAY: (f"[{GRAY_ICON}]●[/{GRAY_ICON}]  [i]Unknown. Retrying..."),
}

PING_INTERVAL: float = 5.0


class ConnectionStatus(Static):
    """Main dashboard widget to asynchronously poll LMS API connectivity and display status."""

    status: reactive[str] = reactive(Connection.YELLOW)
    server_ip: reactive[str] = reactive("192.168.1.1")
    server_port: reactive[int] = reactive(1234)
    api_key: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        app_config = getattr(self.app, "config", None)
        if app_config:
            assert isinstance(app_config, AppConfig)
            self.server_ip = app_config.target
            self.server_port = app_config.port
        else:
            self.post_message(ActionLogUpdate("Could not load config.toml", "warn"))
            default_config = AppConfig().load()
            assert isinstance(default_config, AppConfig)
            self.server_ip = default_config.target
            self.server_port = default_config.port

        self.api_key = SecretsManager.get_api_key(self.server_ip, self.server_port)

        self.update_connection_status()
        self.set_interval(PING_INTERVAL, self.update_connection_status)

    def render(self) -> str:
        status_text: str = CONNECT_STATUS.get(
            self.status, CONNECT_STATUS[Connection.GRAY]
        )
        server_display: str = f"\n\nServer:  {self.server_ip}:{self.server_port}"
        return status_text + server_display

    @work(exclusive=True)
    async def update_connection_status(self) -> None:
        """Check server API status and update reactive state."""

        is_connected: bool = await check_server_status(
            self.server_ip, self.server_port, self.api_key, timeout=PING_INTERVAL
        )
        if is_connected:
            # Check if previously connected
            if self.status != Connection.GREEN:
                self.post_message(ServerConnected(self.server_ip, self.server_port))
            self.status = Connection.GREEN
        else:
            self.status = Connection.RED

    def apply_new_server(self, ip_conf: tuple[str, int] | None) -> None:
        """Update ConnectionStatus display widget with passed net config."""

        if not ip_conf:
            return

        ip, port = ip_conf
        self.server_ip = ip
        self.server_port = port
        self.post_message(ActionLogUpdate(f"Connecting to {ip}:{port}..."))
        self.reset_status()
        self.update_connection_status()

    def reset_status(self) -> None:
        """Force yellow status when switching servers."""

        self.status = Connection.YELLOW

    # ========== ACTIONS ==========
