"""ASGI middleware loading and base types."""

from __future__ import annotations

import importlib
from collections.abc import Awaitable, Callable
from typing import Any

ASGIApp = Callable[
    [dict[str, Any], Callable[..., Awaitable[Any]], Callable[..., Awaitable[Any]]],
    Awaitable[None],
]


def import_string(path: str) -> Any:
    module_path, _, attr = path.rpartition(".")
    if not module_path:
        msg = f"Invalid import path: {path}"
        raise ImportError(msg)
    module = importlib.import_module(module_path)
    return getattr(module, attr)


def build_middleware_stack(app: ASGIApp, middleware_paths: list[str]) -> ASGIApp:
    """Wrap *app* with middleware (last listed = outermost, Django-style)."""
    stack = app
    for path in reversed(middleware_paths):
        middleware_cls = import_string(path)
        stack = middleware_cls(stack)
    return stack
