"""Route matching and parameter extraction."""

from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, get_type_hints
from urllib.parse import parse_qs

from rusjango.schema import Schema

_PATH_PARAM = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


@dataclass(frozen=True)
class Route:
    method: str
    pattern: str
    handler: Callable[..., Awaitable[Any]]
    regex: re.Pattern[str]
    param_names: tuple[str, ...]


def compile_route(method: str, pattern: str, handler: Callable[..., Awaitable[Any]]) -> Route:
    param_names: list[str] = []

    def repl(match: re.Match[str]) -> str:
        param_names.append(match.group(1))
        return r"(?P<" + match.group(1) + r">[^/]+)"

    regex_pattern = "^" + _PATH_PARAM.sub(repl, pattern) + "$"
    return Route(
        method=method.upper(),
        pattern=pattern,
        handler=handler,
        regex=re.compile(regex_pattern),
        param_names=tuple(param_names),
    )


def parse_query_string(query_string: bytes) -> dict[str, str]:
    if not query_string:
        return {}
    parsed = parse_qs(query_string.decode("latin-1"), keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def coerce_param(value: str, annotation: Any) -> Any:
    if annotation is int:
        return int(value)
    if annotation is float:
        return float(value)
    if annotation is bool:
        return value.lower() in ("1", "true", "yes", "on")
    return value


async def call_handler(
    route: Route,
    path_params: dict[str, str],
    query_params: dict[str, str],
    body: Any,
) -> Any:
    hints = get_type_hints(route.handler)
    sig = inspect.signature(route.handler)
    kwargs: dict[str, Any] = {}

    for name, param in sig.parameters.items():
        if name in path_params:
            kwargs[name] = coerce_param(path_params[name], hints.get(name, str))
        elif name in query_params:
            kwargs[name] = coerce_param(query_params[name], hints.get(name, str))

    if body is not None:
        remaining = [p for p in sig.parameters if p not in kwargs]
        if len(remaining) == 1:
            pname = remaining[0]
            ann = hints.get(pname)
            if isinstance(body, dict) and ann is not None:
                if isinstance(ann, type) and issubclass(ann, Schema):
                    kwargs[pname] = ann.from_dict(body)
                else:
                    kwargs[pname] = body
            else:
                kwargs[pname] = body
        elif isinstance(body, dict):
            for key, value in body.items():
                if key in sig.parameters and key not in kwargs:
                    ann = hints.get(key)
                    if isinstance(ann, type) and issubclass(ann, Schema):
                        kwargs[key] = ann.from_dict(body)
                    else:
                        kwargs[key] = value

    return await route.handler(**kwargs)
