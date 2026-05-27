"""ASGI request/response helpers."""

from __future__ import annotations

import json
from typing import Any

from rusjango.exceptions import HTTPException, error_envelope


async def read_body(receive: Any) -> bytes:
    body = b""
    while True:
        message = await receive()
        if message["type"] == "http.request":
            body += message.get("body", b"")
            if not message.get("more_body"):
                break
        elif message["type"] == "http.disconnect":
            break
    return body


def parse_json_body(body: bytes) -> Any:
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(422, detail=f"Invalid JSON: {exc}") from exc


async def send_json(
    send: Any,
    status: int,
    data: Any,
    *,
    headers: dict[str, str] | None = None,
) -> None:
    body = json.dumps(data, default=str).encode("utf-8")
    hdrs = [(b"content-type", b"application/json; charset=utf-8")]
    if headers:
        hdrs.extend((k.lower().encode(), v.encode()) for k, v in headers.items())
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": hdrs,
        }
    )
    await send({"type": "http.response.body", "body": body})


async def send_error(send: Any, exc: HTTPException) -> None:
    label = {
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
    }.get(exc.status_code, "Error")
    await send_json(
        send,
        exc.status_code,
        error_envelope(exc.status_code, label, detail=exc.detail),
        headers=exc.headers,
    )
