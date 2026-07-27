from textual import work
from textual.widgets import Static
from enum import StrEnum

from lm_tuio.api import check_server_status


# Connection status indicator enums and consts.
class Connection(StrEnum):
    GREEN = 'green'
    YELLOW = 'yellow'
    RED = 'red'
    GRAY = 'gray'

CONNECT_STATUS: dict[str, str] = {
    Connection.GREEN: ("[green]●[/green]  Connected"),
    Connection.YELLOW: ("[yellow]●[/yellow]  Connecting..."),
    Connection.RED: ("[tomato]●[/tomato]  Disconnected. Retrying..."),
    Connection.GRAY: ("[lightgray]●[/lightgray]  Unknown. Retrying...")
}

PING_INTERVAL: float = 2.0

# TODO: Connect to config parser for CLI input
# TODO: Take input from change server screen
class ConnectionStatus(Static):
    '''Main dashboard widget to asynchronously poll LMS API connectivity and display status.'''

    def on_mount(self) -> None:
        self.server_ip: str = '192.168.1.100'
        self.server_port: int = 1234
        self.action_set_status(Connection.YELLOW)
        self.set_interval(PING_INTERVAL, self.update_connection_status)


    @work(exclusive=True)
    async def update_connection_status(self) -> None:
        '''Update Header UI with connection status at PING_INTERVAL'''
        is_connected: bool = await check_server_status(self.server_ip, self.server_port, PING_INTERVAL)
        if is_connected:
            self.action_set_status(Connection.GREEN)
        else:
            self.action_set_status(Connection.RED)


    # ========== ACTIONS ==========

    def action_set_status(self, status: str) -> None:
        '''Dynamic HeaderIcon update based on connection to LM Studio server.'''
        text: str
        if status in Connection:
            text = CONNECT_STATUS[status]
        else:
            text = CONNECT_STATUS[Connection.GRAY]

        # self.styles.color = color
        self.update(f"{text}\n\nServer:  {self.server_ip}:{self.server_port}")
