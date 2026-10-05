"""Security middleware."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit


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

        if not debug:
            host = _get_host(scope)
            if not host or not _host_allowed(host, allowed_hosts):
                from rusjango.asgi import send_error
                from rusjango.exceptions import HTTPException

                await send_error(
                    send_wrapper,
                    HTTPException(400, detail=f"Invalid host header: {host}"),
                )
                return

        await self.app(scope, receive, send_wrapper)


def _get_host(scope: dict[str, Any]) -> str | None:
    values = [value for key, value in scope.get("headers", []) if key == b"host"]
    if len(values) != 1:
        return None
    host = values[0].decode("latin-1")
    if any(char.isspace() or char in "/\\@?#" for char in host):
        return None
    try:
        parsed = urlsplit("//" + host)
        parsed.port  # Validate port syntax and range, even when only matching the hostname.
        if host.startswith("[") and "]" in host:
            suffix = host[host.index("]") + 1 :]
            if suffix and not suffix.startswith(":"):
                return None
        return parsed.hostname.rstrip(".") if parsed.hostname else None
    except ValueError:
        return None


def _host_allowed(host: str, allowed: list[str]) -> bool:
    host = host.lower()
    for entry in allowed:
        entry = entry.lower()
        if entry == "*" or host == entry:
            return True
        if entry.startswith(".") and (host == entry[1:] or host.endswith(entry)):
            return True
    return False
