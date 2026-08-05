"""Loads keybinds.toml from config directory, or creates defaults if missing."""

from pathlib import Path
from typing import Any

from textual.binding import Binding
import tomlkit

DEFAULT_KEYMAP: dict[str, dict[str, dict[str, Any]]] = {
    "global": {
        "quit": {"keys": ["q", "ctrl+c"], "desc": "<quit>", "show": True},
        "change_server": {"keys": ["c"], "desc": "<change endpoint>", "show": True},
        "refresh_models": {"keys": ["r"], "desc": "<refresh models>", "show": True},
        "filter": {"keys": ["/"], "desc": "<filter>", "show": True},
        "clear_filter": {
            "keys": ["escape", "ctrl+left_square_bracket"],
            "desc": "<clr filter>",
            "show": False,
        },
        "test_connection": {
            "keys": ["*"],
            "desc": "<test connection>",
            "show": False,
        },
        "show_keybinds": {
            "keys": ["?"],
            "desc": "<hotkeys>",
            "show": True,
        },
        "focus_left": {
            "keys": ["ctrl+h", "ctrl+left"],
            "desc": "<focus pane left>",
            "show": False,
        },
        "focus_right": {
            "keys": ["ctrl+l", "ctrl+right"],
            "desc": "<focus pane right>",
            "show": False,
        },
        "focus_up": {
            "keys": ["ctrl+k", "ctrl+up"],
            "desc": "<focus header log>",
            "show": False,
        },
        "focus_down": {
            "keys": ["ctrl+j", "ctrl+down"],
            "desc": "<focus main area>",
            "show": False,
        },
    },
    "tables": {
        "cursor_up": {
            "keys": ["up", "k", "alt+p"],
            "desc": "<cursor up>",
            "show": False,
        },
        "cursor_down": {
            "keys": ["down", "j", "alt+n"],
            "desc": "<cursor down>",
            "show": False,
        },
        "sort_on_name": {"keys": ["n"], "desc": "<sort name>", "show": True},
        "sort_on_size": {"keys": ["s"], "desc": "<sort size>", "show": True},
    },
    "loaded_models": {
        "unload_selected": {
            "keys": ["u"],
            "desc": "<unload selected>",
            "show": True,
        },
        "unload_all": {"keys": ["U"], "desc": "<unload all>", "show": True},
        "select_model": {"keys": ["space"], "desc": "<select model>", "show": False},
        "toggle_group": {
            "keys": ["x"],
            "desc": "<select group>",
            "show": False,
        },
        "select_up": {
            "keys": ["up", "k", "alt+p"],
            "desc": "<cursor up>",
            "show": False,
        },
        "select_down": {
            "keys": ["down", "j", "alt+n"],
            "desc": "<cursor down>",
            "show": False,
        },
    },
    "action_log": {
        "scroll_up": {
            "keys": ["up", "k", "alt+p"],
            "desc": "<scroll up>",
            "show": False,
        },
        "scroll_down": {
            "keys": ["down", "j", "alt+n"],
            "desc": "<scroll down>",
            "show": False,
        },
        "sort_on_name": {"keys": ["n"], "desc": "<sort name>", "show": True},
        "sort_on_size": {"keys": ["s"], "desc": "<sort size>", "show": True},
    },
    "server_select": {
        "quit": {
            "keys": ["q", "escape"],
            "desc": "<cancel>",
            "show": True,
        },
        "connect_input_submit": {"keys": ["c"], "desc": "<connect>", "show": True},
        "scan_network": {"keys": ["s"], "desc": "<scan>", "show": True},
        "save_defaults": {"keys": ["ctrl+s"], "desc": "<save defaults>", "show": True},
        "clear_cache": {"keys": ["x"], "desc": "<clear cache>", "show": True},
        "select_up": {
            "keys": ["up", "k", "alt+p"],
            "desc": "<cursor up>",
            "show": False,
        },
        "select_down": {
            "keys": ["down", "j", "alt+n"],
            "desc": "<cursor down>",
            "show": False,
        },
    },
}


class KeymapManager:
    """Loads and manages application keybinds from keybinds.toml."""

    _keymap_cache: dict[str, Any] | None = None
    _config_path: Path = Path("keybinds.toml")

    @classmethod
    def load_keymap(cls) -> dict[str, Any]:
        """Loads keybinds.toml or initializes default keybinds if missing."""
        if cls._keymap_cache is not None:
            return cls._keymap_cache

        if not cls._config_path.exists():
            cls._write_default_file()
            cls._keymap_cache = DEFAULT_KEYMAP
            return cls._keymap_cache

        try:
            with open(cls._config_path, "r", encoding="utf-8") as f:
                parsed = tomlkit.load(f)
                cls._keymap_cache = dict(parsed)
        except Exception:
            cls._keymap_cache = DEFAULT_KEYMAP

        return cls._keymap_cache

    @classmethod
    def get_bindings(cls, scope: str) -> list[Binding]:
        """Returns list of Binding objects for a specific scope."""
        keymap = cls.load_keymap()
        scope_data = keymap.get(scope, DEFAULT_KEYMAP.get(scope, {}))

        bindings: list[Binding] = []

        for action_name, config in scope_data.items():
            keys = config.get("keys", [])
            # Support str and list keys dict values to avoid errors
            if isinstance(keys, str):
                keys = [keys]

            desc = config.get("desc", action_name)
            show_footer = config.get("show", True)

            for idx, key in enumerate(keys):
                # Only first key in key list shows in footer when show = true
                should_show = show_footer if idx == 0 else False
                bindings.append(
                    Binding(
                        key=key,
                        action=action_name,
                        description=desc,
                        show=should_show,
                    )
                )

        return bindings

    @classmethod
    def _write_default_file(cls) -> None:
        """Writes the default keymap to disk if it doesn't exist."""
        try:
            doc = tomlkit.document()
            for scope, actions in DEFAULT_KEYMAP.items():
                table = tomlkit.table()
                for action_name, data in actions.items():
                    table[action_name] = data
                doc[scope] = table

            with open(cls._config_path, "w", encoding="utf-8") as f:
                f.write(tomlkit.dumps(doc))
        except Exception:
            pass  # TODO: Log exceptions on config write
