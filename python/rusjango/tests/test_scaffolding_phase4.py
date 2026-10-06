"""Feature file preservation, runnable scaffolds, and production configuration."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("feature", ["docker", "tests"])
def test_feature_removal_preserves_modified_and_unrelated_files(
    command, tmp_path, feature
):
    command("new", "sample")
    root = tmp_path / "sample"
    before = (root / "settings.py").read_bytes(), (root / "pyproject.toml").read_bytes()
    command("add", feature, cwd=root)
    manifest = root / ".rusjango-features.json"
    entries = json.loads(manifest.read_text())["features"][feature]
    command("add", feature, cwd=root)
    changed = root / next(iter(entries))
    changed.write_text("# custom file\n")
    result = command("remove", feature, "--yes", cwd=root)
    assert "Preserved modified file" in result.stdout
    assert changed.read_text() == "# custom file\n"
    assert not manifest.exists()
    assert all(not (root / name).exists() for name in entries if root / name != changed)
    assert before == (
        (root / "settings.py").read_bytes(),
        (root / "pyproject.toml").read_bytes(),
    )


@pytest.mark.parametrize(
    "feature,conflict", [("docker", "Dockerfile"), ("tests", "tests/conftest.py")]
)
def test_conflict_preflight_does_not_partially_scaffold(
    command, tmp_path, feature, conflict
):
    command("new", "sample")
    root = tmp_path / "sample"
    existing = root / conflict
    existing.parent.mkdir(exist_ok=True)
    existing.write_text("# my existing file\n")
    command("add", feature, cwd=root, success=False)
    assert existing.read_text() == "# my existing file\n"
    assert not (root / ".rusjango-features.json").exists()
    assert not (
        root / ("compose.yml" if feature == "docker" else "tests/test_health.py")
    ).exists()


def test_generated_tests_use_memory_database_and_leave_real_database_untouched(
    command, tmp_path
):
    command("new", "sample")
    root = tmp_path / "sample"
    command("add", "app", "school", cwd=root)
    command("add", "orm", cwd=root)
    command("add", "tests", cwd=root)
    database = root / "db.sqlite3"
    database.write_bytes(b"production sentinel - never connect")
    (root / "tests/test_students.py").write_text("""import pytest
@pytest.mark.asyncio
async def test_create(client):
    response = await client.request("POST", "/api/school/students", json={"name":"Sara"})
    assert response.status == 200 and response.json()["id"] == 1
@pytest.mark.asyncio
async def test_separate_database(client):
    response = await client.request("GET", "/api/school/students")
    assert response.json() == []
""")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=root,
        env=command.env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "3 passed" in result.stdout
    assert database.read_bytes() == b"production sentinel - never connect"
    command("remove", "tests", "--yes", cwd=root)
    assert (root / "tests/test_students.py").exists()


def test_docker_settings_and_migrations_respect_production_database_and_custom_paths(
    command, tmp_path
):
    command("new", "sample")
    root = tmp_path / "sample"
    (root / "settings.py").rename(root / "custom.py")
    for name in ("main.py", "pyproject.toml"):
        path = root / name
        path.write_text(path.read_text().replace("settings.py", "custom.py"))
    command("add", "app", "school", cwd=root)
    command("add", "orm", cwd=root)
    command("add", "docker", cwd=root)
    command.env.update(
        RUSJANGO_SETTINGS="settings_docker.py",
        ALLOWED_HOSTS="example.com",
        DATABASE_NAME=str(root / "production.sqlite3"),
    )
    command("migrate", cwd=root)
    assert (root / "production.sqlite3").exists()
    assert not (root / "db.sqlite3").exists()
    script = """import asyncio
from docker_app import app
assert app.settings["DEBUG"] is False
assert app.settings["ALLOWED_HOSTS"] == ["example.com"]
async def check(host):
    output=[]
    async def send(message): output.append(message)
    async def receive(): return {"type":"http.request","body":b"","more_body":False}
    await app({"type":"http","method":"GET","path":"/","query_string":b"","headers":[(b"host",host)]},receive,send)
    return output[0]["status"]
assert asyncio.run(check(b"example.com")) == 200
assert asyncio.run(check(b"evil.example")) == 400
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env=command.env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    env = {key: value for key, value in command.env.items() if key != "ALLOWED_HOSTS"}
    result = subprocess.run(
        [sys.executable, "-c", "import docker_app"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0 and "Set ALLOWED_HOSTS" in result.stderr


def test_tampered_manifest_cannot_remove_outside_files(command, tmp_path):
    command("new", "sample")
    root = tmp_path / "sample"
    command("add", "docker", cwd=root)
    outside = tmp_path / "outside.py"
    outside.write_text("keep me")
    manifest = root / ".rusjango-features.json"
    data = json.loads(manifest.read_text())
    data["features"]["docker"]["../outside.py"] = "keep me"
    manifest.write_text(json.dumps(data))
    command("remove", "docker", "--yes", cwd=root, success=False)
    assert outside.read_text() == "keep me"
    assert (root / "Dockerfile").exists()


def test_both_clis_share_templates_and_ownership(tmp_path):
    binary = os.environ.get("RUSJANGO_RUST_CLI")
    if not binary:
        pytest.skip("Set RUSJANGO_RUST_CLI for cross-CLI scaffolding")
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    python = [sys.executable, "-m", "rusjango"]
    subprocess.run(
        [*python, "new", "sample"],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
    )
    root = tmp_path / "sample"
    subprocess.run(
        [*python, "add", "docker"], cwd=root, env=env, check=True, capture_output=True
    )
    first = json.loads((root / ".rusjango-features.json").read_text())["features"][
        "docker"
    ]
    subprocess.run(
        [binary, "remove", "docker", "--yes"],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [binary, "add", "docker"], cwd=root, env=env, check=True, capture_output=True
    )
    second = json.loads((root / ".rusjango-features.json").read_text())["features"][
        "docker"
    ]
    assert first == second
    subprocess.run(
        [*python, "remove", "docker", "--yes"],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
    )
    assert not (root / "Dockerfile").exists()


def test_feature_removal_keeps_other_scaffold(command, tmp_path):
    command("new", "sample")
    root = tmp_path / "sample"
    command("add", "docker", cwd=root)
    command("add", "tests", cwd=root)
    command("remove", "docker", "--yes", cwd=root)
    assert (root / "tests/test_health.py").exists()
    assert set(
        json.loads((root / ".rusjango-features.json").read_text())["features"]
    ) == {"tests"}


def test_symlinked_test_directory_is_not_modified(command, tmp_path):
    command("new", "sample")
    root = tmp_path / "sample"
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / "tests").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks unavailable on this platform")
    command("add", "tests", cwd=root, success=False)
    assert not list(outside.iterdir())


def test_schema_override_does_not_configure_bare_app(monkeypatch, tmp_path):
    from rusjango import Rusjango
    from rusjango.orm import configure_db

    settings = tmp_path / "alternate.py"
    settings.write_text("DEBUG = False\nDATABASE = None\n")
    monkeypatch.setenv("RUSJANGO_SETTINGS", str(settings))
    assert Rusjango(settings="nonexistent.py").settings["DEBUG"] is False
    assert Rusjango().settings == {}
    configure_db(None)


def test_malformed_app_config_does_not_write_feature_files(command, tmp_path):
    command("new", "sample")
    root = tmp_path / "sample"
    path = root / "pyproject.toml"
    path.write_text(path.read_text().replace('app = "main:app"', 'app = "invalid"'))
    command("add", "docker", cwd=root, success=False)
    assert not (root / "Dockerfile").exists()
    assert not (root / ".rusjango-features.json").exists()
