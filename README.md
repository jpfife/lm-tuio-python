# lm-tuio

A modern TUI for managing LM Studio Servers over the network via API - load, download, and unload models in a terminal window.

> **Built with [Textual](https://textual.textualize.io/)**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Keybinds](#keybinds)
- [Development Guide](#development-guide)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

1. **Install uv**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/jpfife/lm-tuio-python.git
   cd lm-tuio
   ```

3. **Run the app**:
   ```bash
   uv sync
   uv run lm-tuio
   ```

---

## Features

- **Local Network Discovery** - Automated subnet scan for LM Studio Server endpoints
- **Model Management** - Load/unload models with per-instance parameters (context length, flash attention, KV cache offload, eval batch size, num experts)
- **HuggingFace Integration** - Download models directly from HuggingFace URLs or LM Studio catalog IDs
- **API Key Management** - Manage and store per-endpoint API keys
- **IP Cache** - Remember recent server connections across sessions
- **Action Log** - Full history of all application operations with system clipboard
- **Filter/Search** - Live filter on displayed model lists
- **Configurable** - TOML-based configuration for defaults, network scan subnets, and custom keybinds
- **Cross-Platform** - Works on Windows, macOS, and Linux

---

## Installation

### From Source (Recommended)

```bash
git clone https://github.com/your-username/lm-tuio.git
cd lm-tuio
uv sync
```
Optional: install dev dependencies
```bash
uv sync --extra dev
```

### Running the Application

```bash
uv run lm-tuio
```

---

## Usage

### Launching the App

```bash
uv run lm-tuio
```

LM TUIO opens with default loopback endpoint and LM Studio Server port (127.0.0.1:1234) and writes default missing configuration files (see below).
Once in the app, hotkey `c` brings up the Select Server screen to connect to your API endpoint. Alternatively, you can set your endpoint IP, port, and API key (optional) via the CLI. See [CLI arguments](#command-line-interface).

Subsequent launches will reference your defaults set in `config.toml`

Configuration Path: $XDG_CONFIG_HOME/lm-tuio/
Configuration Files:
- config.toml
- keymap.toml
- secrets.toml (API keys)

### Command-Line Interface

| Argument | Description |
|----------|-------------|
| `IP:PORT` | Connect directly to this server (bypasses modal) |
| `-n, --network SUBNET` | Scan this subnet for active LM Studio instances |
| `-p, --port PORT` | Specify port to scan/connect on (default: 1234) |

#### Examples:

```bash
# Connect directly on launch (if defaults are not set)
uv run lm-tuio -t 192.168.1.10 -p 10100 -k sk-lm-mysecret:key

# Set default subnet for network API endpoint scans
uv run lm-tuio -n 10.0.0.0/8 -p 8080

# Help
uv run lm-tuio --help
```

*(If connect via CLI flags, open the `change server` screen with `c` and save your defaults for persistence)*

---

## Configuration Files (TOML)

Configuration is stored in the user's home directory:

```
~/.config/lm-tuio/
├── config.toml     # Default connection settings, scan subnets
├── keymap.toml     # Custom keybind mappings per screen scope
└── secrets.toml    # Per-endpoint API keys
```

### Config Schema (`config.toml`)

```toml
# Default connection target (shown on first launch)
target = "192.168.1.0/24"
port = 1234

# Network scan defaults
scan_subnet = "192.168.1.0/24"   # CIDR notation for subnet scanning
scan_port = 1234

# Remembered server connections (most recent first)
cached_ips = [
    "192.168.1.10:1234",
    "192.168.1.11:1234",
]

# Maximum IP cache entries to keep in memory
total_cached_ips = 10
```

### Keymap Schema (`keybinds.toml`)

Each section corresponds to a Textual screen scope (defined in `src/lm_tuio/config/keymap.py`). Each action maps keys to actions with descriptions:
`show = true` means the hotkey will display in the app footer when the associated screen is focused.

LM TUIO uses tomlkit to read/write the default keymap to keybinds.toml in the format below:
```toml
[global.quit]
keys = ["q", "ctrl+c"]
desc = "<quit>"
show = true

[global.change_server]
keys = ["c"]
desc = "<change endpoint>"
show = true
```

However, this format is equally valid and can be parsed by LM TUIO just fine:
```toml
[global]
quit = { keys = ["q", "ctrl+c"], desc = "<quit>", show = true }
change_server = { keys = ["c"], desc = "<change endpoint>", show = true }
download_model = { keys = ["d"], desc = "<download>", show = true }
```

### Secrets Schema (`secrets.toml`)

API keys are stored per-endpoint:

```toml
[192.168.1.10:1234]
api_key = "sk-xxxxxxxxxxxxxx"  # redacted in docs

[192.168.1.11:8080]
api_key = "sk-yyyyyyyyyyyyyy"
```

> **Security Note:** The secrets file is stored unencrypted, but sets read/write permissions for the user only.

---

## Keybinds

Press `?` at any time to view the full keybind reference. Here are the most common shortcuts:

| Key / Combo | Action |
|-------------|--------|
| **q** / **ctrl+q** | Quit application |
| `/` | Toggle filter on model lists (enter search mode) |
| **l** | Load selected model from *downloaded models* list |
| **u** | Unload selected model instance(s) |
| **d** | Open modal to download new model from HuggingFace |
| **c** | Change server connection (open Server Selection Modal) |
| `*` | Retest API connection status |
| **h/j/k/l** | Move focus between main panes (VIM-style) |
| **j/k/↑↓** | Navigate within tables/lists |
| **Tab** / **Shift+Tab** | Move focus between widgets (accessibility) |
| **Enter** | Confirm selection in modals, trigger default action |
| **Esc** | Cancel filter/search or dismiss modal |
| `?` | View all available keybinds |

---

## Development Guide

### Setting Up the Environment

```bash
# Clone repository
git clone https://github.com/your-username/lm-tuio.git
cd lm-tuio

# Create virtual environment with uv (recommended)
uv venv --python 3.14  # or your preferred Python version
uv sync                 # Install project + dependencies
uv run python -m pip install pytest  # if not included
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output and coverage
uv run pytest --verbose --cov=src/lm_tuio --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_config.py -v
```

### Code Style & Conventions

The project follows these standards:

- **Formatting:** Use `ruff` or `black` (configure in pyproject.toml)
- **Type hints:** All public functions use full type annotations
- **Docstrings:** Every module, class, and function has a brief docstring
- **Commit messages:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)

### Adding New Features

1. **Create the feature branch**
   ```bash
   git switch -c feat/new-feature
   ```

2. **Add your implementation code** (preferably in a new module under `src/lm_tuio/`)

3. **Update type hints and docstrings** - every public API must have documentation

4. **Write tests** (if applicable) - place test files in `tests/` with matching names

5. **Run the linter and formatter**
   ```bash
   uv run ruff check src/lm_tuio --fix
   uv run black src/lm_tuio
   ```

6. **Commit changes**
   ```bash
   git add -A
   git commit -m "feat: add something cool and needed"
   ```

### Adding a New Screen (Modal or Full)

1. Create `src/lm_tuio/screens/my_new_screen.py`
2. Extend `ModalScreen` (for popups) or `Screen` (for full-screen)
3. Define bindings using `KeymapManager.get_bindings("my_scope")`
4. Implement `compose()` with Textual widgets
5. Register in `config/keymap.toml`
6. Push from dashboard: `self.app.push_screen(MyNewScreen())`

---

## Contributing

Contributions welcome! How you can help:

### Issue Tracker
- **Report bugs:** Use the [Bug Report Template](https://github.com/your-username/lm-tuio/issues/new?template=bug_report.md)
- **Request features:** Use the [Feature Request Template](https://github.com/your-username/lm-tuio/issues/new?template=feature_request.md)

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git switch -c feature/new-feature`)
3. Make your changes (add tests if applicable)
4. Ensure all CI checks pass (run locally with `uv run pytest`)
5. Submit a pull request with:
   - Clear description of what you changed
   - Link to relevant issues (e.g., "Fixes #123")
   - Screenshots of UI changes if applicable

---

## License

This project is licensed under the MIT License — see [LICENSE.txt](LICENSE.txt) for details.

---

**Made using [Textual](https://textual.textualize.io/) and Python.**
