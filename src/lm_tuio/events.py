"""Event manager for application updates and state changes."""

from textual.message import Message


class ServerEndpointUpdated(Message):
    """Fires when selecting new server or network config changes."""

    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        super().__init__()
