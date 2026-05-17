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


pkg_resources = types.ModuleType("pkg_resources")
setattr(pkg_resources, "DistributionNotFound", DistributionNotFound)
setattr(pkg_resources, "require", _require)
sys.modules["pkg_resources"] = pkg_resources


if __name__ == "__main__":
    getattr(importlib.import_module("vint"), "main")()
