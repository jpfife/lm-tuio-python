"""Loads keybinds.toml from config directory, or creates defaults if missing."""

from pathlib import Path
from typing import Any

from textual.binding import Binding
import tomlkit

from lm_tuio.config import paths


KEYBIND_CONFIG: str = "keybinds.toml"

DEFAULT_KEYMAP: dict[str, dict[str, dict[str, Any]]] = {
    "global": {
        "quit": {"keys": ["q", "ctrl+c"], "desc": "<quit>", "show": True},
        "change_server": {"keys": ["c"], "desc": "<change endpoint>", "show": True},
        "refresh_models": {"keys": ["r"], "desc": "<refresh>", "show": True},
        "download_model": {"keys": ["d"], "desc": "<download>", "show": True},
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
        "unload_all": {"keys": ["U"], "desc": "<unload all>", "show": True},
        "show_action_log": {"keys": ["L"], "desc": "<log viewer>", "show": True},
        "show_keybinds": {
            "keys": ["?"],
            "desc": "<hotkeys>",
            "show": True,
        },
        "focus_left": {
            "keys": ["ctrl+h", "left", "ctrl+left", "alt+h"],
            "desc": "<focus pane left>",
            "show": False,
        },
        "focus_right": {
            "keys": ["ctrl+l", "right", "ctrl+right", "alt+l"],
            "desc": "<focus pane right>",
            "show": False,
        },
        "focus_up": {
            "keys": ["ctrl+k", "ctrl+up", "alt+k"],
            "desc": "<focus header log>",
            "show": False,
        },
        "focus_down": {
            "keys": ["ctrl+j", "ctrl+down", "alt+j"],
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
        "load_model": {"keys": ["return"], "desc": "<load model>", "show": True},
        "sort_on_name": {"keys": ["n"], "desc": "<sort name>", "show": False},
        "sort_on_size": {"keys": ["s"], "desc": "<sort size>", "show": False},
    },
    "loaded_models": {
        "unload_selected": {
            "keys": ["u"],
            "desc": "<unload selected>",
            "show": True,
        },
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
    },
    "action_log_viewer": {
        "quit": {
            "keys": ["q", "escape"],
            "desc": "<close>",
            "show": True,
        },
        "copy_to_clipboard": {
            "keys": ["c", "y"],
            "desc": "<copy to clipboard>",
            "show": True,
        },
        "scroll_up": {
            "keys": ["up", "k", "alt+p"],
            "desc": "<scroll up>",
            "show": True,
        },
        "scroll_down": {
            "keys": ["down", "j", "alt+n"],
            "desc": "<scroll down>",
            "show": True,
        },
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
    "download_models": {
        "quit": {
            "keys": ["q", "escape"],
            "desc": "<cancel>",
            "show": True,
        },
    },
}


class KeymapManager:
    """Loads and manages application keybinds from keybinds.toml."""

    _keymap_cache: dict[str, Any] | None = None

    @classmethod
    def load_keymap(cls) -> dict[str, Any]:
        """Loads keybinds.toml or initializes default keybinds if missing."""
        if cls._keymap_cache is not None:
            return cls._keymap_cache

        config_path = paths.get_config_path(KEYBIND_CONFIG)

        if not config_path.exists():
            cls._write_default_file(config_path)
            cls._keymap_cache = DEFAULT_KEYMAP
            return cls._keymap_cache

        try:
            with open(config_path, "r", encoding="utf-8") as f:
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
    def _write_default_file(cls, path: Path) -> None:
        """Writes the default keymap to disk if it doesn't exist."""
        try:
            doc = tomlkit.document()
            for scope, actions in DEFAULT_KEYMAP.items():
                table = tomlkit.table()
                for action_name, data in actions.items():
                    table[action_name] = data
                doc[scope] = table

            with open(path, "w", encoding="utf-8") as f:
                f.write(tomlkit.dumps(doc))
        except Exception:
            pass  # TODO: Log exceptions on config write
