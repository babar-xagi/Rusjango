"""Install a wheel into a fresh environment and exercise its native module/CLI."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile


SMOKE = """
import asyncio
import importlib.metadata
import json
import rusjango
from main import app
from rusjango.orm import close_db

assert rusjango._core is not None
assert rusjango.__version__ == importlib.metadata.version("rusjango")

async def request(method, body=b""):
    messages = []
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    async def send(message):
        messages.append(message)
    await app({"type": "http", "method": method, "path": "/api/school/students",
               "query_string": b"", "headers": [(b"host", b"localhost")]}, receive, send)
    return messages[0]["status"], json.loads(messages[1]["body"])

async def main():
    try:
        status, created = await request("POST", b'{"name":"Ali"}')
        assert status == 200 and isinstance(created["id"], int) and created["age"] is None
        assert (await request("GET"))[1] == [created]
        assert (await request("POST", b'{"name":123}'))[0] == 422
    finally:
        await close_db()

asyncio.run(main())
print("Installed wheel: native version, scaffold, migration, CRUD, and validation passed")
"""


def main() -> None:
    wheel = Path(sys.argv[1]).resolve()
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT"}
    }
    with tempfile.TemporaryDirectory(prefix="rusjango-wheel-") as directory:
        root = Path(directory)
        venv = root / "venv"
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(venv)], check=True, env=env
        )
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), str(wheel)],
            check=True,
            env=env,
        )
        subprocess.run(
            [str(python), "-m", "rusjango", "new", "demo"],
            cwd=root,
            env=env,
            check=True,
        )
        project = root / "demo"
        for args in [["add", "app", "school"], ["add", "orm"], ["migrate"]]:
            subprocess.run(
                [str(python), "-m", "rusjango", *args], cwd=project, env=env, check=True
            )
        subprocess.run([str(python), "-c", SMOKE], cwd=project, env=env, check=True)


if __name__ == "__main__":
    main()
