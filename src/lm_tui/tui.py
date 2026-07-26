from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable
from lm_tui.api import fetch_available_models, check_server_status
from lm_tui.models import ModelInfo, QuantizationInfo


PING_INTERVAL: float = 2.0
CONNECT_STATUS: dict[str, str] = {
    'green': "[green] ● ",
    'yellow': "[yellow] ● ",
    'red': "[red] ● "
}

class LMStudioApp(App):
    '''Main Textual application for LM Studio TUI.'''
    BINDINGS = [
        ('q', 'quit', "[quit]"),
        ('r', 'refresh_models', "[refresh list]")
    ]

    # Accept target IP and port from CLI on load.
    def __init__(self, ip: str, port: int):
        super().__init__()
        self.target_ip: str = ip
        self.target_port: int = port


    def compose(self) -> ComposeResult:
        '''Yields widgets to draw on screen.'''
        self.header = Header(show_clock=True)
        yield self.header
        yield Footer()
        yield DataTable(id='models_table')


    async def on_mount(self) -> None:
        '''Sets table and fetches data on first load.'''
        table = self.query_one(DataTable)
        table.add_columns(
            "Model Name",
            "Architecture",
            "Size (GB)",
            "Quantization",
            "API Key"
        )
        table.cursor_type = 'row'

        self.title = f"LM Studio Dashboard - {self.target_ip}:{self.target_port}"
        self.sub_title = " Connecting..."
        self.header.icon = CONNECT_STATUS['yellow']

        await self.action_refresh_models()
        self.set_interval(PING_INTERVAL, self.update_connection_status)

    async def update_connection_status(self) -> None:
        '''Update Header UI with connection status at PING_INTERVAL'''
        is_connected: bool = await check_server_status(self.target_ip, self.target_port)

        if is_connected:
            self.header.icon = CONNECT_STATUS['green']
            self.sub_title = " Connected - Available Models"
        else:
            self.header.icon = CONNECT_STATUS['red']
            self.sub_title = " Disconnected. Retrying..."


    async def action_refresh_models(self) -> None:
        """Triggered by 'r' key binding and on_mount()"""
        table = self.query_one(DataTable)
        table.clear()
        
        self.title = f"LM Studio Dashboard - {self.target_ip}:{self.target_port}"
        self.sub_title = " Fetching..."

        models: list[ModelInfo] | None
        err: str | None
        models, err = await fetch_available_models(self.target_ip, self.target_port)
        
        if err:
            self.sub_title = f" API Error: {err}"
            self.header.icon = CONNECT_STATUS['red']
            return

        if models:
            self.header.icon = CONNECT_STATUS['green']
            self.sub_title = " Connected - Available Models"
            for model in models:
                assert isinstance(model, ModelInfo)
                arch: str = model.architecture or "Unknown"     # Handle optional field
                quant: QuantizationInfo | str = model.quantization if model.quantization else "None"
                size_gb: str = f"{model.size_bytes / (1024 ** 3):.2f}"

                table.add_row(
                    model.display_name,
                    arch,
                    size_gb,
                    quant,
                    model.key
                )
