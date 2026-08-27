"""Manage API key storage and access using SECRETS_FILE file.

Check for SECRETS_FILE reads, updates, or creates if not found.
Set SECRETS_FILE permissions to 0600 for an illusion of security.
"""

import os
from pathlib import Path
import stat
from typing import Any

import tomlkit

from lm_tuio.config import paths


SECRETS_FILE: str = "secrets.toml"
ENCODING: str = "utf-8"
SERVERS_TABLE: str = "servers"


class SecretsManager:
    """Handle read/write ops for SECRETS_FILE and set 0600 POSIX permissions."""

    _secrets_cache: dict[str, Any] | None = None
    header_str: str = "# LM TUIO API keys\n\n[servers]\n"

    @classmethod
    def _check_file_and_secure(cls, filepath: Path) -> None:
        """Create file/mod perms if missing."""

        if not filepath.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding=ENCODING) as file:
                file.write(cls.header_str)

            os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)
        else:
            # Check correct perms/set if incorrect
            current_perms = stat.S_IMODE(os.stat(filepath).st_mode)
            if current_perms != (stat.S_IRUSR | stat.S_IWUSR):
                os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)

    @classmethod
    def load_secrets(cls) -> dict[str, Any]:
        """Load API keys from SECRETS_FILE"""

        if cls._secrets_cache is not None:
            return cls._secrets_cache

        secrets_path: Path = paths.get_config_path(SECRETS_FILE)
        cls._check_file_and_secure(secrets_path)

        try:
            with open(secrets_path, "r", encoding=ENCODING) as file:
                parsed = tomlkit.load(file)
                cls._secrets_cache = dict(parsed)
        except Exception:
            cls._secrets_cache = {SERVERS_TABLE: {}}

        return cls._secrets_cache

    @classmethod
    def get_api_key(cls, ip: str, port: int) -> str:
        """Retrieve API key for specific endpoint [IP:Port]."""

        secrets: dict[str, Any] = cls.load_secrets()
        endpoint: str = f"{ip}:{port}"

        servers_table: dict = secrets.get(SERVERS_TABLE, {})
        server_data: dict = servers_table.get(endpoint, {})
        return server_data.get("api_key") or ""

    @classmethod
    def save_api_key(cls, ip: str, port: int, api_key: str) -> None:
        """Save or update API key for a specific endpoint."""

        secrets_path: Path = paths.get_config_path(SECRETS_FILE)
        cls._check_file_and_secure(secrets_path)

        endpoint: str = f"{ip}:{port}"

        try:
            with open(secrets_path, "r", encoding=ENCODING) as file:
                doc = tomlkit.load(file)
        except Exception:
            doc = tomlkit.document()

        if SERVERS_TABLE not in doc:
            doc.add(SERVERS_TABLE, tomlkit.table())

        servers_table = doc[SERVERS_TABLE]

        if endpoint not in servers_table:
            servers_table.add(endpoint, tomlkit.table())

        server_entry = servers_table[endpoint]
        if api_key:
            server_entry["api_key"] = api_key
        elif "api_key" in server_entry:
            del server_entry["api_key"]  # Remove API key if empty string passed

        with open(secrets_path, "w", encoding=ENCODING) as file:
            file.write(tomlkit.dumps(doc))

        cls._secrets_cache = dict(doc)

    @classmethod
    def remove_endpoints(cls, endpoints: list[str]) -> None:
        """Remove the specified endpoints from secrets.toml."""

        secrets_path = paths.get_config_path(SECRETS_FILE)
        if not secrets_path.exists():
            return

        try:
            with open(secrets_path, "r", encoding=ENCODING) as file:
                doc = tomlkit.load(file)
        except Exception:
            return

        servers_table = doc.get(SERVERS_TABLE)
        if not servers_table:
            return

        changed = False
        for endpoint in endpoints:
            if endpoint in servers_table:
                del servers_table[endpoint]
                changed = True

        if changed:
            with open(secrets_path, "w", encoding=ENCODING) as file:
                file.write(tomlkit.dumps(doc))
            cls._secrets_cache = dict(doc)
