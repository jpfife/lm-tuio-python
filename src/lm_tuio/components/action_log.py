"""Live log feed and action status widget for primary dashboard."""

from datetime import datetime
from zoneinfo import ZoneInfo

from textual.widgets import RichLog


class ActionLog(RichLog):
    """Header widget for real-time app and API telemetry."""

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
                tag = "[bold red]ERR[/]"
            case "warning" | "warn":
                tag = "[bold yellow]WRN[/]"
            case "success" | "ok":
                tag = "[bold green]OK [/]"
            case _:
                tag = "[bold cyan]INF[/]"

        self.history.append((timestamp, severity, message))

        self.write(f"[dim]{timestamp}[/] {tag} {message}")
