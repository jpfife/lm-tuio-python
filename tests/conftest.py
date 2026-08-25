"""Shared pytest fixtures for lm-tuio tests."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_cwd(tmp_path: Path):
    """Mock Path.cwd() to return a temp directory without config.toml.

    This ensures that get_config_path() doesn't find a local config.toml
    in the repo root during tests, making tests portable across machines.
    """
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        yield


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Session-scoped temp config directory shared across test classes."""
    return tmp_path / ".config" / "lm-tuio"


@pytest.fixture
def secrets_manager(secrets_manager_class, tmp_config_dir: Path):
    """Provide a fresh SecretsManager with isolated cache and patched paths."""
    from lm_tuio.config.secrets import SecretsManager

    # Clear the class-level cache before each test
    original_cache = SecretsManager._secrets_cache
    SecretsManager._secrets_cache = None

    manager = secrets_manager_class()

    # Patch get_config_path to return path under tmp_config_dir
    with patch(
        "lm_tuio.config.secrets.paths.get_config_path",
        side_effect=lambda filename: tmp_config_dir / filename,
    ):
        yield manager

    SecretsManager._secrets_cache = original_cache


@pytest.fixture
def secrets_manager_class():
    """Provide the SecretsManager class for testing."""
    from lm_tuio.config.secrets import SecretsManager
    return SecretsManager


@pytest.fixture
def tmp_config_dir_path(tmp_path: Path) -> Path:
    """Session-scoped temp config directory path (for tests that need it directly)."""
    return tmp_path / ".config" / "lm-tuio"
