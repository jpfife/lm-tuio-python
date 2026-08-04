"""Event manager for application updates and state changes."""

from textual.message import Message

from lm_tuio.models import ModelInfo


class ServerEndpointUpdated(Message):
    """Fires when selecting new server or network config changes."""

    def __init__(self, ip: str, port: int) -> None:
        super().__init__()
        self.ip = ip
        self.port = port


class ServerConnected(Message):
    """Fired when ConnectionStatus widget successfully pings server."""

    def __init__(self, ip: str, port: int) -> None:
        super().__init__()
        self.ip = ip
        self.port = port


class ModelSelected(Message):
    """Fired when model is highlighted in Loaded/Downloaded Models lists."""

    def __init__(self, model: ModelInfo | None) -> None:
        super().__init__()
        self.model = model


class UnloadInstancesRequested(Message):
    """Fired when user requests unload of one or more instances."""

    def __init__(self, instance_ids: list[str]) -> None:
        super().__init__()
        self.instance_ids = instance_ids
