"""Route matching and parameter extraction."""

from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, get_type_hints
from urllib.parse import parse_qs

from rusjango.exceptions import HTTPException
from rusjango.schema import Schema, SchemaValidationError, validate_value

_PATH_PARAM = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


@dataclass(frozen=True)
class Route:
    method: str
    pattern: str
    handler: Callable[..., Awaitable[Any]]
    regex: re.Pattern[str]
    param_names: tuple[str, ...]


def compile_route(
    method: str, pattern: str, handler: Callable[..., Awaitable[Any]]
) -> Route:
    param_names: list[str] = []

    parts: list[str] = []
    position = 0
    for match in _PATH_PARAM.finditer(pattern):
        name = match.group(1)
        if name in param_names:
            raise ValueError(f"Duplicate path parameter: {name}")
        param_names.append(name)
        parts.extend(
            [re.escape(pattern[position : match.start()]), f"(?P<{name}>[^/]+)"]
        )
        position = match.end()
    parts.append(re.escape(pattern[position:]))
    regex_pattern = "^" + "".join(parts) + "$"
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
        lowered = value.lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
        raise ValueError("Expected boolean")
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

    for name in sig.parameters:
        ann = hints.get(name, str)
        is_body = isinstance(ann, type) and (issubclass(ann, Schema) or ann is dict)
        source = "path" if name in path_params else "query"
        values = path_params if source == "path" else query_params
        if name in values and not is_body:
            try:
                kwargs[name] = coerce_param(values[name], ann)
            except (ValueError, TypeError) as exc:
                raise HTTPException(
                    422,
                    detail=[
                        {
                            "loc": [source, name],
                            "msg": f"Invalid {getattr(ann, '__name__', ann)}",
                        }
                    ],
                ) from exc

    remaining = [name for name in sig.parameters if name not in kwargs]
    body_params = [
        name
        for name in remaining
        if isinstance(hints.get(name), type)
        and (issubclass(hints[name], Schema) or hints[name] is dict)
    ]
    try:
        if len(body_params) == 1:
            name = body_params[0]
            ann = hints[name]
            if (
                body is not None
                or sig.parameters[name].default is inspect.Parameter.empty
            ):
                kwargs[name] = validate_value(body, ann, ["body", name])
        elif body is not None and len(remaining) == 1:
            name = remaining[0]
            kwargs[name] = validate_value(body, hints.get(name, Any), ["body", name])
        elif isinstance(body, dict):
            for name in remaining:
                if name in body:
                    kwargs[name] = validate_value(
                        body[name], hints.get(name, Any), ["body", name]
                    )
    except SchemaValidationError as exc:
        raise HTTPException(422, detail=exc.errors) from exc

    missing = [
        name
        for name, param in sig.parameters.items()
        if name not in kwargs and param.default is inspect.Parameter.empty
    ]
    if missing:
        raise HTTPException(
            422,
            detail=[
                {"loc": ["query", name], "msg": "Field is required"} for name in missing
            ],
        )

    return await route.handler(**kwargs)
