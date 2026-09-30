"""Shared repository location and bounded CLI calls for contract tests."""

import functools
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the test checkout independently of the shell cwd."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def run_command() -> Callable[..., subprocess.CompletedProcess[str]]:
    """Capture a CLI result with a timeout; accept subprocess.run overrides."""
    return functools.partial(
        subprocess.run,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
