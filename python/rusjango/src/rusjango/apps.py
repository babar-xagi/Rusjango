"""Discover and mount INSTALLED_APPS API routers."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rusjango.app import Rusjango


def load_installed_apps(app: Rusjango) -> None:
    """Import each app's ``api`` module and mount its router under ``/api/<name>``."""
    for dotted in app.settings.get("INSTALLED_APPS") or []:
        if not dotted or not isinstance(dotted, str):
            continue
        if dotted in app._loaded_apps:
            continue
        short_name = dotted.rsplit(".", 1)[-1]
        api_module = importlib.import_module(f"{dotted}.api")
        sub_router: Rusjango = api_module.router
        prefix = f"/api/{short_name}"
        app.include_router(sub_router, prefix=prefix)
        app._loaded_apps.add(dotted)

    if app.settings.get("DATABASE"):
        for dotted in app.settings.get("INSTALLED_APPS") or []:
            if not dotted or not isinstance(dotted, str):
                continue
            try:
                importlib.import_module(f"{dotted}.models")
            except ModuleNotFoundError as exc:
                if exc.name != f"{dotted}.models":
                    raise
