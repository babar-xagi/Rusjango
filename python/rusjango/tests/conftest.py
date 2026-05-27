"""Shared test helpers."""

from __future__ import annotations

import json
from typing import Any

from rusjango import Rusjango


async def call_asgi(
    app: Rusjango,
    method: str = "GET",
    path: str = "/",
    query: str = "",
    body: bytes = b"",
) -> tuple[int, dict[str, Any]]:
    scope: dict[str, Any] = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": query.encode() if query else b"",
        "headers": [],
    }
    messages: list[dict[str, Any]] = []
    body_sent = False

    async def receive() -> dict[str, Any]:
        nonlocal body_sent
        if body_sent:
            return {"type": "http.disconnect"}
        body_sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await app(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    resp_body = next(m for m in messages if m["type"] == "http.response.body")["body"]
    return start["status"], json.loads(resp_body)
