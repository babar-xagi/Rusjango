"""Shared test helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
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


@pytest.fixture(params=["python", "rust"])
def command(request, tmp_path):
    if request.param == "rust":
        binary = os.environ.get("RUSJANGO_RUST_CLI")
        if not binary:
            pytest.skip("Set RUSJANGO_RUST_CLI to exercise the compiled Rust CLI")
        prefix = [str(Path(binary).resolve())]
    else:
        prefix = [sys.executable, "-m", "rusjango"]
    env = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).parents[1] / "src"),
        "UV_PROJECT_ENVIRONMENT": sys.prefix,
        "UV_NO_SYNC": "1",
        "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"],
    }

    def run(*args, cwd=tmp_path, success=True):
        result = subprocess.run(
            [*prefix, *args], cwd=cwd, env=env, capture_output=True, text=True
        )
        assert (result.returncode == 0) == success, result.stdout + result.stderr
        return result

    run.env = env
    return run
