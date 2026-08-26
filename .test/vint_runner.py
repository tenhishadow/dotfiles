"""Run vim-vint without requiring setuptools in the project environment."""

from __future__ import annotations

import importlib
import importlib.metadata
import sys
import types


class DistributionNotFound(Exception):
    """Compatibility exception used by vim-vint."""


def _require(name: str) -> list[types.SimpleNamespace]:
    try:
        return [types.SimpleNamespace(version=importlib.metadata.version(name))]
    except importlib.metadata.PackageNotFoundError as exc:
        raise DistributionNotFound(name) from exc


def _install_pkg_resources_shim() -> None:
    pkg_resources = types.ModuleType("pkg_resources")
    pkg_resources.__dict__["DistributionNotFound"] = DistributionNotFound
    pkg_resources.__dict__["require"] = _require
    sys.modules["pkg_resources"] = pkg_resources


def main() -> None:
    """Install the compatibility shim and delegate to vim-vint."""
    _install_pkg_resources_shim()
    importlib.import_module("vint").main()


if __name__ == "__main__":
    main()
