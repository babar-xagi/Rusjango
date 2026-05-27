"""Load project settings.py as a plain dict."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def load_settings(path: str | Path) -> dict[str, Any]:
    """Import settings module and return public uppercase settings."""
    settings_path = Path(path).resolve()
    if not settings_path.is_file():
        msg = f"Settings file not found: {settings_path}"
        raise FileNotFoundError(msg)

    spec = importlib.util.spec_from_file_location("rusjango_settings", settings_path)
    if spec is None or spec.loader is None:
        msg = f"Cannot load settings: {settings_path}"
        raise ImportError(msg)

    module = ModuleType("rusjango_settings")
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    return {
        key: getattr(module, key)
        for key in dir(module)
        if key.isupper() and not key.startswith("_")
    }
