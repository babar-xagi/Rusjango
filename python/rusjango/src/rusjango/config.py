"""Load [tool.rusjango] from pyproject.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from *start* (or cwd) until pyproject.toml contains [tool.rusjango]."""
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file() and _has_rusjango_tool(pyproject):
            return directory
    msg = "No Rusjango project found (missing [tool.rusjango] in pyproject.toml)"
    raise FileNotFoundError(msg)


def load_rusjango_config(project_root: Path | None = None) -> dict[str, Any]:
    root = project_root or find_project_root()
    pyproject = root / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    return data.get("tool", {}).get("rusjango", {})


def _has_rusjango_tool(pyproject: Path) -> bool:
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    return "rusjango" in data.get("tool", {})
