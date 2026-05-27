"""Rusjango — Rust-powered async Python web framework."""

from rusjango.app import Rusjango
from rusjango.exceptions import HTTPException
from rusjango.router import router
from rusjango.schema import Schema

# Router is a per-app Rusjango instance — use this in every apps/*/api.py
# instead of the module-level `router` singleton.
Router = Rusjango

__version__ = "0.1.0"

try:
    from rusjango import _core as _core  # noqa: F401 — maturin-built extension

    __version__ = getattr(_core, "__version__", __version__)
except ImportError:
    _core = None  # type: ignore[misc, assignment]

__all__ = ["Rusjango", "Router", "router", "HTTPException", "Schema", "__version__"]
