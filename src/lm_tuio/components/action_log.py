"""Live log feed and action status widget for primary dashboard."""

from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from textual.widgets import RichLog

from lm_tuio.config import keymap


class LogColor(StrEnum):
    ERR = "[bold red]"
    WARN = "[bold yellow]"
    OK = "[bold green]"
    INF = "[bold cyan]"


class ActionLog(RichLog):
    """Header widget for real-time app and API telemetry."""

    BINDINGS = keymap.KeymapManager.get_bindings("action_log")

    history: list[tuple[str, str, str]]
    timezone: str
    zone_tz: ZoneInfo

    def __init__(self, timezone: str = "America/New_York", *args, **kwargs) -> None:
        super().__init__(
            *args, highlight=True, markup=True, wrap=True, max_lines=500, **kwargs
        )

        self.history = []  # Timestamp, severity, msg
        self.timezone = timezone
        self.zone_tz = ZoneInfo(timezone)

    def add_entry(self, message: str, severity: str = "info") -> None:
        """Write timestamped/color-coded entry to the log."""
        timestamp = datetime.now(tz=self.zone_tz).strftime("%H:%M:%S")

        match severity.lower():
            case "error" | "err":
                tag = f"{LogColor.ERR}ERR[/]"
            case "warning" | "warn":
                tag = f"{LogColor.WARN}WRN[/]"
            case "success" | "ok":
                tag = f"{LogColor.OK}OK [/]"
            case _:
                tag = f"{LogColor.INF}INF[/]"

        self.history.append((timestamp, severity, message))

        self.write(f"[dim]{timestamp}[/] {tag} {message}")

    # ======= ACTIONS =======

    def action_scroll_up(self) -> None:
        self.scroll_up()

    def action_scroll_down(self) -> None:
        self.scroll_down()
