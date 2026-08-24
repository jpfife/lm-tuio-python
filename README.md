# lm-tuio

A TUI for managing LM Studio Servers over the network via API - load, unload, and download models without SSH.

> **Built with [Textual](https://textual.textualize.io/)**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick Start

**Install uv**
```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Run without intalling**
```bash
uvx lm-tuio
```

**Or install globally and run**
```bash
uv tool install lm-tuio
lm-tuio
```


## Features

- **Local Network Discovery** - Automated subnet scan for LM Studio Server endpoints
- **Model Management** - Load/unload models with per-instance parameters (context length, flash attention, KV cache offload, eval batch size, num experts)
- **HuggingFace Integration** - Download models directly from HuggingFace URLs or LM Studio catalog IDs
- **API Key Management** - Manage and store per-endpoint API keys
- **IP Cache** - Remember recent server connections across sessions
- **Action Log** - Full history of all application operations with system clipboard
- **Filter/Search** - Live filter on displayed model lists
- **Configurable** - TOML-based configuration for defaults, network scan subnets, and custom keybinds
- **Cross-Platform** - Works on Windows, macOS, and Linux, and anywhere you can install python

## Installation

```bash
# uv
uv tool install lm-tuio
```

```bash
# pip - Linux / macOS
python -m pip lm-tuio
```
```bash
# pip - Windows
py -m pip lm-tuio
```

### From Source (for development)

```bash
git clone https://github.com/jpfife/lm-tuio-python.git
cd lm-tuio
uv sync --extra dev
```

## Usage

LM TUIO opens with default loopback endpoint and LM Studio Server port (127.0.0.1:1234) and writes default missing configuration files (see below).
Once in the app, hotkey `c` brings up the Select Server screen to connect to your API endpoint. 

Alternatively, you can set your endpoint IP, port, and API key (optional) via the CLI.

Subsequent launches will reference your defaults set in `config.toml`

### Command-Line Interface

| Argument | Description |
|----------|-------------|
| `-h, --help` | Display help information and exit |
| `-c, --config-file FILE\|PATH` | Use specified config file or create config directory |
| `-k, --api-key KEY` | Set API key for initial connection (requires --target and --port) |
| `-t, --target IP` | Set target server IP address |
| `-n, --network SUBNET` | Scan this subnet for active LM Studio instances |
| `-p, --port PORT` | Specify port to scan/connect on (default: 1234) |
| `-T, --theme THEME` | Set theme (textual-dark, gruvbox, dracula, etc. |
| `-Z, --timezone TZ` | Set timezone for log timestamps (e.g., America/Los_Angeles |

#### Examples:

```bash
# Connect directly on launch (if defaults are not set)
lm-tuio -t 192.168.1.10 -p 10100 -k sk-lm-mysecret:key

# Set default subnet for network API endpoint scans
lm-tuio -n 10.0.0.0/8 -p 8080

# Set configuration file for current session (non-persistent)
lm-tuio -c ~/new/dir/config.toml

# Set/create configuration directory for current session
lm-tuio -c ~/new/dir/

# Add alias to your environment (.bashrc, .zshrc, etc.) for persisting config
alias lm-tuio='lm-tuio -c ~/new/dir/'
```
> [!NOTE]
> If connect via CLI flags, open the `change server` screen with `c` and save your defaults for persistence

!!!! ADD GIF EXAMPLE SET CONFIG !!!!

## Configuration

Configuration Path: $XDG_CONFIG_HOME/lm-tuio/ (typically ~/.config/lm-tuio/)

```
~/.config/lm-tuio/
├── config.toml     # Default connection settings, scan subnets
├── keymap.toml     # Custom keybind mappings per screen scope
└── secrets.toml    # Per-endpoint API keys
```

### Config Schema (`config.toml`)

Default configurations are grouped by table. 

### Keymap Schema (`keybinds.toml`)

Each section corresponds to a Textual screen scope (defined in `src/lm_tuio/config/keymap.py`). Each action maps keys to actions with descriptions:
`show = true` means the hotkey will display in the app footer when the associated screen is focused.

LM TUIO uses tomlkit to read/write the default keymap to keybinds.toml in the format below:
```toml
[global.quit]
keys = ["q", "ctrl+q"]
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
quit = { keys = ["q", "ctrl+c"], desc = "quit", show = true }
change_server = { keys = ["c"], desc = "change endpoint", show = true }
download_model = { keys = ["d"], desc = "download", show = true }
```

### Secrets Schema (`secrets.toml`)

API keys are stored per-endpoint:

```toml
[192.168.1.10:1234]
api_key = "sk-xxxxxxxxxxxxxx"

[192.168.1.11:8080]
api_key = "sk-yyyyyyyyyyyyyy"
```

> **Security Note:** The secrets file is stored unencrypted, but sets read/write permissions for the user only.

## Keybinds

Press `?` at any time to view the full keybind reference. Here are the most common shortcuts:

### General
| Key | Action |
|-------------|--------|
| `q` / `ctrl+q` | Quit application |
| `/` | Toggle filter on model lists (enter search mode) |
| `Esc` / `Ctrl+\[` | Cancel filter/search or dismiss pop-up |
| `Enter` | Confirm selection, load highlighted model |
| `c` | Change connected server/endpoint |
| `l` | Load selected model from *downloaded models* list |
| `U` | Unload all loaded models |
| `u` | Unload selected model instance(s) |
| `d` | Download new model from HuggingFace |
| `*` | Retest API connection |
| `g` | Open settings menu |
| `?` | View all available keybinds |

### Navigation
| Key | Action |
|-------------|--------|
| `Ctrl+` \[`↑` / `↓` / `←` / `→`\] | Move focus between main panes |
| `Ctrl+` / `Alt+` \[`h` / `j` / `k` / `l`\] | Alternate move focus between main panes |
| `↑` / `↓` / `j` / `k` | Navigate within tables/lists |
| `Tab` / `Shift+Tab` | Move focus between widgets |

## Contributing

Contributions welcome! How you can help:

### Issue Tracker
- **Report bugs:** Open a new issue!
- **Request features:** Also a new issue!

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git switch -c feature/new-feature`)
3. Make your changes (add tests if applicable)
4. Ensure all CI checks pass (run locally with `uv run pytest`)
5. Submit a pull request with:
   - Clear description of what you changed
   - Link to relevant issues (e.g., "Fixes #123")
   - Screenshots of UI changes if applicable

## License

This project is licensed under the MIT License — see [LICENSE.txt](LICENSE.txt) for details.

**Made using [Textual](https://textual.textualize.io/) and Python.**
