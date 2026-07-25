from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable
from textual.coordinate import Coordinate
from lm_tui.api import fetch_available_models
from lm_tui.models import ModelInfo, QuantizationInfo


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
        yield Header(show_clock=True)
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
        await self.action_refresh_models()


    async def action_refresh_models(self) -> None:
        """Triggered by 'r' key binding and on_mount()"""
        table = self.query_one(DataTable)
        table.clear()
        
        self.title = f"LM Studio Dashboard - {self.target_ip}:{self.target_port}"
        self.sub_title = "Fetching..."

        models: list[ModelInfo] | None
        err: str | None
        models, err = await fetch_available_models(self.target_ip, self.target_port)
        
        if err:
            self.sub_title = f"Error: {err}"
            return

        if models:
            self.sub_title = "Available Models"
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
