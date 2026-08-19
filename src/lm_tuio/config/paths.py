"""XDG config path resolution with local directory fallback (for development)."""

import os
from pathlib import Path


def get_config_path(filename: str) -> Path:
    """Resolve config path for settings functions.
    Prefer local file in current working directory, else use ~/.config/lm-tuio"""
    local_path = Path.cwd() / filename
    if local_path.exists():
        return local_path

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        config_dir = Path(xdg_config_home) / "lm-tuio"
    else:
        config_dir = Path.home() / ".config" / "lm-tuio"

    # Make config directory if missing
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / filename
