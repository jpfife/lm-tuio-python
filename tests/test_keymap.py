"""Tests for ../src/lm_tuio/config/keymap.py.

Tests KeymapManager load, fallback, get_bindings, _write_default_file.
"""

from pathlib import Path
from unittest.mock import patch

from textual.binding import Binding

from lm_tuio.config import KeymapManager
from lm_tuio.config.keymap import DEFAULT_KEYMAP


class TestKeymapManagerLoad:
    """Test KeymapManager.load_keymap() and fallback behavior."""

    def test_returns_cache_on_second_call(self):
        """Second call returns cached value without re-reading."""
        result1 = KeymapManager.load_keymap()
        result2 = KeymapManager.load_keymap()
        assert result1 is result2  # same object (cached)

    def test_loads_default_when_file_missing(self, tmp_config_dir: Path):
        """Missing keybinds.toml returns DEFAULT_KEYMAP."""
        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=tmp_config_dir / "keybinds.toml",
        ):
            keymap = KeymapManager.load_keymap()

        assert keymap is not None
        assert "global" in keymap
        assert "tables" in keymap
        assert "loaded_models" in keymap

    def test_loads_from_file_when_exists(self, tmp_config_dir: Path):
        """Existing keybinds.toml is parsed and returned."""
        kb_file = tmp_config_dir / "keybinds.toml"
        kb_file.parent.mkdir(parents=True, exist_ok=True)
        kb_file.write_text(
            '[global]\nquit = { keys = ["q", "ctrl+c"], desc = "<quit>", show = true }\n'
        )

        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=kb_file,
        ):
            keymap = KeymapManager.load_keymap()

        assert keymap is not None
        assert "global" in keymap
        assert "quit" in keymap["global"]
        assert keymap["global"]["quit"]["keys"] == ["q", "ctrl+c"]

    def test_fallback_on_malformed_toml(self, tmp_config_dir: Path):
        """Malformed TOML falls back to DEFAULT_KEYMAP."""
        kb_file = tmp_config_dir / "keybinds.toml"
        kb_file.parent.mkdir(parents=True, exist_ok=True)
        kb_file.write_text("[global\n")  # missing ]

        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=kb_file,
        ):
            keymap = KeymapManager.load_keymap()

        assert keymap is not None
        assert "global" in keymap
        assert "quit" in keymap["global"]

    def test_fallback_on_empty_file(self, tmp_config_dir: Path):
        """Empty file returns default keymap."""
        kb_file = tmp_config_dir / "keybinds.toml"
        kb_file.parent.mkdir(parents=True, exist_ok=True)
        kb_file.write_text("")

        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=kb_file,
        ):
            keymap = KeymapManager.load_keymap()

        assert keymap is not None
        assert "global" in keymap


class TestKeymapManagerGetBindings:
    """Test KeymapManager.get_bindings() per scope."""

    def test_returns_bindings_for_global_scope(self):
        """get_bindings('global') returns Binding objects."""
        bindings = KeymapManager.get_bindings("global")
        assert isinstance(bindings, list)
        assert len(bindings) > 0
        for b in bindings:
            assert isinstance(b, Binding)

    def test_returns_bindings_for_tables_scope(self):
        """get_bindings('tables') returns Binding objects."""
        bindings = KeymapManager.get_bindings("tables")
        assert isinstance(bindings, list)
        assert len(bindings) > 0
        for b in bindings:
            assert isinstance(b, Binding)

    def test_returns_bindings_for_loaded_models_scope(self):
        """get_bindings('loaded_models') returns Binding objects."""
        bindings = KeymapManager.get_bindings("loaded_models")
        assert isinstance(bindings, list)
        assert len(bindings) > 0
        for b in bindings:
            assert isinstance(b, Binding)

    def test_returns_bindings_for_action_log_scope(self):
        """get_bindings('action_log') returns Binding objects."""
        bindings = KeymapManager.get_bindings("action_log")
        assert isinstance(bindings, list)
        assert len(bindings) > 0
        for b in bindings:
            assert isinstance(b, Binding)

    def test_returns_bindings_for_unknown_scope(self):
        """Unknown scope returns empty list."""
        bindings = KeymapManager.get_bindings("nonexistent_scope")
        assert isinstance(bindings, list)
        assert len(bindings) == 0

    def test_binding_has_correct_attributes(self):
        """Each Binding has key, action, description, show."""
        bindings = KeymapManager.get_bindings("global")
        quit_bindings = [b for b in bindings if b.action == "quit"]
        assert len(quit_bindings) > 0
        for b in quit_bindings:
            assert b.key is not None
            assert b.action == "quit"
            assert b.description is not None

    def test_multiple_keys_per_action(self):
        """Actions with multiple keys each get separate Binding objects."""
        bindings = KeymapManager.get_bindings("global")
        focus_left_bindings = [b for b in bindings if b.action == "focus_left"]
        # focus_left has 4 keys: ctrl+h, left, ctrl+left, alt+h
        assert len(focus_left_bindings) == 4


class TestKeymapManagerWriteDefaultFile:
    """Test _write_default_file writes correct TOML."""

    def test_writes_default_file(self, tmp_config_dir: Path):
        """_write_default_file creates a valid TOML file."""
        kb_file = tmp_config_dir / "keybinds.toml"
        kb_file.parent.mkdir(parents=True, exist_ok=True)
        KeymapManager._write_default_file(kb_file)

        assert kb_file.exists()
        content = kb_file.read_text()
        assert "[global.quit]" in content
        assert "[tables.cursor_up]" in content

    def test_writes_all_scopes(self, tmp_config_dir: Path):
        """All DEFAULT_KEYMAP scopes are written."""
        kb_file = tmp_config_dir / "keybinds.toml"
        kb_file.parent.mkdir(parents=True, exist_ok=True)
        KeymapManager._write_default_file(kb_file)

        content = kb_file.read_text()
        for scope in [
            "global",
            "tables",
            "loaded_models",
            "action_log",
            "action_log_viewer",
            "server_select",
            "download_models",
            "settings_screen",
        ]:
            assert f"[{scope}." in content

    def test_writes_action_definitions(self, tmp_config_dir: Path):
        """Each scope's actions are written with correct structure."""
        kb_file = tmp_config_dir / "keybinds.toml"
        kb_file.parent.mkdir(parents=True, exist_ok=True)
        KeymapManager._write_default_file(kb_file)

        content = kb_file.read_text()
        assert "quit" in content
        assert "download_model" in content
        assert "cursor_up" in content


class TestKeymapManagerCacheInvalidate:
    """Test cache invalidation behavior."""

    def test_cache_invalidation_allows_update(self, tmp_config_dir: Path):
        """Clearing cache allows re-loading from disk."""
        # Clear any cached value from prior tests
        KeymapManager._keymap_cache = None

        kb_file = tmp_config_dir / "keybinds.toml"
        kb_file.parent.mkdir(parents=True, exist_ok=True)
        kb_file.write_text(
            '[global]\nquit = { keys = ["q"], desc = "<quit>", show = true }\n'
        )

        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=kb_file,
        ):
            keymap1 = KeymapManager.load_keymap()

        # Clear cache
        KeymapManager._keymap_cache = None

        kb_file.write_text(
            '[global]\nquit = { keys = ["Q"], desc = "<quit>", show = true }\n'
        )

        with patch(
            "lm_tuio.config.paths.get_config_path",
            return_value=kb_file,
        ):
            keymap2 = KeymapManager.load_keymap()

        assert keymap1["global"]["quit"]["keys"] == ["q"]
        assert keymap2["global"]["quit"]["keys"] == ["Q"]
        assert keymap1 is not keymap2


class TestKeymapManagerHeader:
    """Test DEFAULT_KEYMAP structure."""

    def test_all_expected_scopes_present(self):
        """All expected scopes are in DEFAULT_KEYMAP."""

        expected_scopes = {
            "global",
            "tables",
            "loaded_models",
            "action_log",
            "action_log_viewer",
            "server_select",
            "load_model_screen",
            "download_models",
            "settings_screen",
            "keymap_screen",
        }
        assert set(DEFAULT_KEYMAP.keys()) == expected_scopes

    def test_each_action_has_required_fields(self):
        """Each action has keys, desc, and show fields."""
        for scope, actions in DEFAULT_KEYMAP.items():
            for action_name, data in actions.items():
                assert "keys" in data, f"{scope}.{action_name} missing 'keys'"
                assert "desc" in data, f"{scope}.{action_name} missing 'desc'"
                assert "show" in data, f"{scope}.{action_name} missing 'show'"
