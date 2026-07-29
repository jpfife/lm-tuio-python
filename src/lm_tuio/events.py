"""Event manager for application updates and state changes."""

from textual.message import Message

from lm_tuio.models import ModelInfo


class ServerEndpointUpdated(Message):
    """Fires when selecting new server or network config changes."""

    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        super().__init__()


class ServerConnected(Message):
    """Fired when ConnectionStatus widget successfully pings server."""

    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        super().__init__()


class ModelSelected(Message):
    """Fired when model is highlighted in Loaded/Downloaded Models lists."""

    def __init__(self, model: ModelInfo | None) -> None:
        self.model = model
        super().__init__()
