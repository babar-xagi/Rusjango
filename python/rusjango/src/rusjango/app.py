"""Application factory and route decorators."""

from __future__ import annotations

import traceback
from collections.abc import Awaitable, Callable
from typing import Any

from rusjango.asgi import parse_json_body, read_body, send_error, send_json
from rusjango.exceptions import HTTPException, error_envelope
from rusjango.middleware import ASGIApp, build_middleware_stack
from rusjango.routing import Route, call_handler, compile_route, parse_query_string
from rusjango.settings import load_settings


def _join_paths(prefix: str, path: str) -> str:
    if not prefix:
        return path
    return f"{prefix.rstrip('/')}/{path.lstrip('/')}"


class Rusjango:
    """Main application object — ASGI 3.0 callable with route decorators."""

    def __init__(self, settings: str | None = None) -> None:
        self.settings_path = settings
        self.settings: dict[str, Any] = load_settings(settings) if settings else {}
        self._routes: list[Route] = []
        self._asgi_app: ASGIApp | None = None
        if self.settings.get("DATABASE"):
            from rusjango.orm.connection import configure_db

            configure_db(self.settings["DATABASE"])

    def get(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        return self._route("GET", path)

    def post(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        return self._route("POST", path)

    def put(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        return self._route("PUT", path)

    def delete(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        return self._route("DELETE", path)

    def _route(
        self, method: str, path: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        def decorator(
            handler: Callable[..., Awaitable[Any]],
        ) -> Callable[..., Awaitable[Any]]:
            self._routes.append(compile_route(method, path, handler))
            self._asgi_app = None
            return handler

        return decorator

    def include_router(self, other: Rusjango, prefix: str = "") -> None:
        """Mount routes from another :class:`Rusjango` instance."""
        for route in other._routes:
            path = _join_paths(prefix, route.pattern)
            self._routes.append(compile_route(route.method, path, route.handler))
        self._asgi_app = None

    def load_installed_apps(self) -> None:
        """Mount routers from ``INSTALLED_APPS`` (``apps.<name>.api:router``)."""
        from rusjango.apps import load_installed_apps as _load

        _load(self)

    def _build_asgi(self) -> ASGIApp:
        if self._asgi_app is not None:
            return self._asgi_app

        async def core(scope: dict[str, Any], receive: Any, send: Any) -> None:
            if scope["type"] != "http":
                return
            scope.setdefault("rusjango", {})["settings"] = self.settings
            method = scope["method"]
            path = scope["path"]
            query = parse_query_string(scope.get("query_string", b""))

            route = self._match(method, path)
            if route is None:
                await send_error(
                    send,
                    HTTPException(404, detail=f"No route for {method} {path}"),
                )
                return

            body_data = None
            if method in ("POST", "PUT", "PATCH"):
                raw = await read_body(receive)
                body_data = parse_json_body(raw)

            match = route.regex.match(path)
            assert match is not None
            path_params = {n: match.group(n) for n in route.param_names}

            try:
                result = await call_handler(route, path_params, query, body_data)
            except HTTPException as exc:
                await send_error(send, exc)
                return
            except Exception:
                if self.settings.get("DEBUG"):
                    await send_json(
                        send,
                        500,
                        error_envelope(
                            500,
                            "Internal Server Error",
                            detail=traceback.format_exc(),
                        ),
                    )
                else:
                    await send_json(
                        send,
                        500,
                        error_envelope(500, "Internal Server Error"),
                    )
                return

            if isinstance(result, dict):
                await send_json(send, 200, result)
            elif isinstance(result, list):
                await send_json(send, 200, result)
            elif result is None:
                await send_json(send, 204, {})
            else:
                await send_json(send, 200, result)

        middleware = self.settings.get("MIDDLEWARE") or []
        self._asgi_app = build_middleware_stack(core, list(middleware))
        return self._asgi_app

    def _match(self, method: str, path: str) -> Route | None:
        for route in self._routes:
            if route.method == method.upper() and route.regex.match(path):
                return route
        return None

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        app = self._build_asgi()
        try:
            await app(scope, receive, send)
        except HTTPException as exc:
            await send_error(send, exc)

    @property
    def route_count(self) -> int:
        return len(self._routes)
