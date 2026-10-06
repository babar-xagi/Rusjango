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
from rusjango import Field, Schema, field_validator
from rusjango.admin import AdminIdentity, AdminPermissionDenied
from main import app
from rusjango.orm import close_db

assert rusjango._core is not None
assert rusjango.__version__ == importlib.metadata.version("rusjango")

class Input(Schema):
    __coerce__ = True
    count: int = Field(ge=1)
    name: str = Field(min_length=2)
    @field_validator("name")
    def trim(value):
        return value.strip()

assert Input(count="2", name=" Ali ").dict() == {"count": 2, "name": "Ali"}

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
        actor = AdminIdentity("staff", frozenset(f"admin:school.student:{action}" for action in ("view", "add", "change", "delete")))
        site = app.admin_site
        assert site.catalog(identity=actor)[0]["label"] == "school.student"
        assert (await site.list("school.student", identity=actor))["items"] == [{"id": created["id"], "name": "Ali"}]
        try:
            await site.list("school.student")
        except AdminPermissionDenied:
            pass
        else:
            raise AssertionError("Unauthenticated admin access accepted")
        added = await site.create("school.student", {"name": "Sara"}, identity=actor)
        assert (await site.update("school.student", added["id"], {"name": "Ada"}, identity=actor))["name"] == "Ada"
        assert await site.delete("school.student", added["id"], identity=actor) == 1
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
        for args in [
            ["add", "app", "school"],
            ["add", "orm"],
            ["migrate"],
            ["add", "docker"],
            ["add", "tests"],
            ["add", "admin"],
        ]:
            subprocess.run(
                [str(python), "-m", "rusjango", *args], cwd=project, env=env, check=True
            )
        settings = project / "settings.py"
        settings.write_text(
            settings.read_text().replace(
                "ADMIN = None", 'ADMIN = {"FACTORY": "admin:create_site"}'
            )
        )
        (
            project / "apps/school/admin.py"
        ).write_text("""from rusjango import Field, Schema
from .models import Student
from .schemas import StudentCreate
class Rename(Schema):
    name: str = Field(min_length=1, max_length=100)
def register(site):
    site.register(Student, list_display=("id", "name"), detail_fields=("id", "name", "age"),
                  create_schema=StudentCreate, update_schema=Rename, allow_delete=True)
""")
        subprocess.run([str(python), "-c", SMOKE], cwd=project, env=env, check=True)
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "pytest",
                "pytest-asyncio",
            ],
            env=env,
            check=True,
        )
        subprocess.run(
            [str(python), "-m", "pytest", "tests", "-q"],
            cwd=project,
            env=env,
            check=True,
        )
        for feature in ("docker", "tests", "admin"):
            subprocess.run(
                [str(python), "-m", "rusjango", "remove", feature, "--yes"],
                cwd=project,
                env=env,
                check=True,
            )


if __name__ == "__main__":
    main()
