"""Exercise generated projects through Python and, when available, Rust CLI."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest


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

    return run


def test_add_remove_two_apps_preserves_settings(command, tmp_path):
    command("new", "sample")
    root = tmp_path / "sample"
    assert {p.name for p in root.iterdir()} == {
        "main.py",
        "settings.py",
        "pyproject.toml",
    }
    command("add", "app", "alpha", cwd=root)
    command("add", "app", "beta", cwd=root)
    settings = {}
    exec((root / "settings.py").read_text(), settings)
    assert settings["INSTALLED_APPS"] == ["apps.alpha", "apps.beta"]
    assert settings["DEBUG"] is True
    assert settings["DATABASE"] is None
    assert settings["MIDDLEWARE"] == ["rusjango.security.SecurityMiddleware"]
    command("remove", "app", "alpha", "--yes", cwd=root)
    settings = {}
    exec((root / "settings.py").read_text(), settings)
    assert settings["INSTALLED_APPS"] == ["apps.beta"]
    assert settings["SECRET_KEY"]
    assert not (root / "apps" / "alpha").exists()


def test_add_orm_preserves_custom_routes_and_disable_preserves_settings(
    command, tmp_path
):
    command("new", "sample")
    root = tmp_path / "sample"
    command("add", "app", "school", cwd=root)
    api = root / "apps" / "school" / "api.py"
    custom = 'from rusjango import Router\nrouter = Router()\n@router.get("/custom")\nasync def custom(): return {}\n'
    api.write_text(custom)
    command("add", "orm", cwd=root)
    assert api.read_text() == custom
    assert (api.parent / "models.py").exists()
    command("remove", "orm", "--yes", cwd=root)
    settings = {}
    exec((root / "settings.py").read_text(), settings)
    assert settings["DATABASE"] is None
    assert settings["AUTH"] is None
    assert settings["INSTALLED_APPS"] == ["apps.school"]
    tomllib.loads((root / "pyproject.toml").read_text())


def test_generated_example_migrates_and_handles_requests(command, tmp_path):
    command("new", "sample")
    root = tmp_path / "sample"
    command("add", "app", "school", cwd=root)
    command("add", "orm", cwd=root)
    command("migrate", cwd=root)
    assert (root / "db.sqlite3").exists()
    script = """
import asyncio, json
from main import app
from rusjango.orm import close_db
async def check():
    messages = []
    async def receive():
        return {"type":"http.request", "body":b'{"name":"Ali"}', "more_body":False}
    async def send(message): messages.append(message)
    try:
        await app({"type":"http", "method":"POST", "path":"/api/school/students",
                   "query_string":b"", "headers":[]}, receive, send)
        assert messages[0]["status"] == 200
        data = json.loads(messages[1]["body"])
        assert data["name"] == "Ali" and data["age"] is None and isinstance(data["id"], int)
    finally:
        await close_db()
asyncio.run(check())
"""
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_apps_added_after_orm_receive_models(command, tmp_path):
    command("new", "sample")
    root = tmp_path / "sample"
    command("add", "orm", cwd=root)
    command("add", "app", "school", cwd=root)
    assert (root / "apps/school/models.py").exists()
    assert "Student.create" in (root / "apps/school/api.py").read_text()
    command("add", "orm", cwd=root)
    command("migrate", cwd=root)


def test_migration_failure_is_nonzero(command, tmp_path):
    command("new", "sample")
    result = command("migrate", cwd=tmp_path / "sample", success=False)
    assert "DATABASE is not configured" in result.stdout + result.stderr


def test_custom_settings_path_and_single_quote_lists(command, tmp_path):
    command("new", "sample")
    root = tmp_path / "sample"
    (root / "settings.py").rename(root / "custom.py")
    project = root / "pyproject.toml"
    project.write_text(
        project.read_text().replace(
            'settings = "settings.py"', 'settings = "custom.py"'
        )
    )
    command("add", "app", "school", cwd=root)
    command("add", "orm", cwd=root)
    command("remove", "orm", "--yes", cwd=root)
    assert not (root / "settings.py").exists()
    settings = {}
    exec((root / "custom.py").read_text(), settings)
    assert settings["INSTALLED_APPS"] == ["apps.school"]
    assert settings["DATABASE"] is None


def test_invalid_app_removal_preserves_project(command, tmp_path):
    command("new", "sample")
    root = tmp_path / "sample"
    before = (root / "settings.py").read_bytes()
    command("remove", "app", "..", "--yes", cwd=root, success=False)
    assert (root / "settings.py").read_bytes() == before


@pytest.mark.parametrize("target", [("add", "app", "school"), ("add", "orm")])
@pytest.mark.parametrize(
    "assignment",
    [
        ("INSTALLED_APPS = []", "INSTALLED_APPS = load_apps()"),
        ("DATABASE = None", "DATABASE = {} | config"),
    ],
)
def test_computed_settings_fail_before_scaffolding(
    command, tmp_path, target, assignment
):
    command("new", "sample")
    root = tmp_path / "sample"
    settings = root / "settings.py"
    before = settings.read_text().replace(*assignment)
    settings.write_text(before)
    command(*target, cwd=root, success=False)
    assert settings.read_text() == before
    assert not (root / "apps").exists()
    assert not (root / "migrations").exists()
