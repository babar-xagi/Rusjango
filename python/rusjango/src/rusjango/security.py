"""Security middleware."""

from __future__ import annotations

from typing import Any

from rusjango.exceptions import HTTPException


class SecurityMiddleware:
    """Basic host validation and security headers."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = scope.get("rusjango", {}).get("settings", {})
        debug = settings.get("DEBUG", False)
        allowed_hosts: list[str] = settings.get("ALLOWED_HOSTS") or []

        if not debug and allowed_hosts:
            host = _get_host(scope)
            if host and not _host_allowed(host, allowed_hosts):
                from rusjango.asgi import send_error
                from rusjango.exceptions import HTTPException

                await send_error(
                    send,
                    HTTPException(400, detail=f"Invalid host header: {host}"),
                )
                return

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                    ]
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)


def _get_host(scope: dict[str, Any]) -> str | None:
    for key, value in scope.get("headers", []):
        if key == b"host":
            return value.decode("latin-1").split(":")[0]
    return None


def _host_allowed(host: str, allowed: list[str]) -> bool:
    host = host.lower()
    for entry in allowed:
        entry = entry.lower()
        if entry == "*" or host == entry:
            return True
        if entry.startswith(".") and host.endswith(entry):
            return True
    return False
