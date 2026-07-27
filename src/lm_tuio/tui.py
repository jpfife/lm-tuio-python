from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable
from textual.widgets._header import HeaderIcon
from enum import StrEnum
from lm_tuio.api import fetch_available_models, check_server_status
from lm_tuio.models import ModelInfo, QuantizationInfo


# Connection status indicator enums and consts.
class Connection(StrEnum):
    GREEN = 'green'
    YELLOW = 'yellow'
    RED = 'red'
    GRAY = 'gray'

CONNECT_STATUS: dict[str, tuple[str, str]] = {
    Connection.GREEN: (" ●   Connected", 'lightgreen'),
    Connection.YELLOW: (" ●   Connecting...", 'yellow'),
    Connection.RED: (" ●   Disconnected. Retrying...", 'tomato'),
    Connection.GRAY: (" ●   Unknown. Retrying...", 'lightgray')
}

PING_INTERVAL: float = 5.0

# Subtitle consts
class Subtitle(StrEnum):
    GET_MODELS = ' Available Models'
    LOAD = ' Load Model'
    UNLOAD = ' Unload Model'
    DOWNLOAD = ' Download Model'
    DL_STATUS = ' Download Status'
    API_ERROR = ' API Error:'


class LMStudioApp(App):
    '''Main Textual application for LM Studio TUI.'''
    BINDINGS = [
        ('q', 'quit', "[quit]"),
        ('r', 'refresh_models', "[refresh list]")
    ]

    CSS_PATH = 'styles.tcss'
    
    # Accept target IP and port from CLI on load.
    def __init__(self, ip: str, port: int):
        super().__init__()
        self.target_ip: str = ip
        self.target_port: int = port
        self.title = f"LM TUIO - LM Studio Dashboard " + \
                f"[{self.target_ip}:{self.target_port}]"


    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, time_format='%H:%M')
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

        self.sub_title = " LM TUIO"
        self.action_set_status(Connection.YELLOW)

        await self.action_refresh_models()
        self.set_interval(PING_INTERVAL, self.update_connection_status)

        header = self.query_one(Header)
        header.tall = True

    # ========== ACTIONS ==========

    def action_set_status(self, status: str) -> None:
        '''Dynamic HeaderIcon update based on connection to LM Studio server.'''
        icon_widget = self.query_one('HeaderIcon', expect_type=HeaderIcon)
        if status in Connection:
            icon_widget.icon, icon_widget.styles.color = CONNECT_STATUS[status]
        else:
            icon_widget.icon, icon_widget.styles.color = CONNECT_STATUS[Connection.GRAY]


    async def action_refresh_models(self) -> None:
        """Triggered by 'r' key binding and on_mount()"""
        table = self.query_one(DataTable)
        table.clear()
        
        self.sub_title = Subtitle.GET_MODELS + " - Fetching..."

        models: list[ModelInfo] | None
        err: str | None
        models, err = await fetch_available_models(self.target_ip, self.target_port)
        
        if err:
            self.sub_title = f" API Error: {err}"
            self.action_set_status(Connection.RED)
            return

        if models:
            self.action_set_status(Connection.GREEN)
            self.sub_title = Subtitle.GET_MODELS
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


    # ========== STATE UPDATES ==========

    async def update_connection_status(self) -> None:
        '''Update Header UI with connection status at PING_INTERVAL'''
        is_connected: bool = await check_server_status(self.target_ip, self.target_port)
        if is_connected:
            self.action_set_status(Connection.GREEN)
        else:
            self.action_set_status(Connection.RED)


