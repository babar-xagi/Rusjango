"""Build and exercise generated Docker scaffolding using the candidate wheel."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid


def main() -> None:
    wheel = Path(sys.argv[1]).resolve()
    project_name = "rusjango-check-" + uuid.uuid4().hex[:12]
    env = {**os.environ, "ALLOWED_HOSTS": "localhost,127.0.0.1", "DATABASE_URL": ""}
    env.pop("RUSJANGO_SETTINGS", None)
    with tempfile.TemporaryDirectory(prefix="rusjango-docker-") as directory:
        root = Path(directory)
        subprocess.run(
            [sys.executable, "-m", "rusjango", "new", "demo"],
            cwd=root,
            env=env,
            check=True,
        )
        project = root / "demo"
        for args in [
            ("add", "app", "school"),
            ("add", "orm"),
            ("add", "docker"),
            ("add", "admin"),
        ]:
            subprocess.run(
                [sys.executable, "-m", "rusjango", *args],
                cwd=project,
                env=env,
                check=True,
            )
        settings = project / "settings.py"
        settings.write_text(
            settings.read_text().replace(
                "ADMIN = None", 'ADMIN = {"FACTORY": "admin:create_site"}'
            )
        )
        (project / "apps/school/admin.py").write_text("""from .models import Student
def register(site):
    site.register(Student, list_display=("id", "name"))
""")
        vendor = project / "vendor"
        vendor.mkdir()
        shutil.copy2(wheel, vendor / wheel.name)
        config = project / "pyproject.toml"
        config.write_text(
            config.read_text()
            + f'\n[tool.uv.sources]\nrusjango = {{ path = "vendor/{wheel.name}" }}\n'
        )
        compose = project / "compose.yml"
        compose.write_text(
            compose.read_text().replace('"8000:8000"', '"127.0.0.1::8000"')
        )
        prefix = ["docker", "compose", "-p", project_name]

        def run(*args, check=True, capture=False):
            return subprocess.run(
                [*prefix, *args],
                cwd=project,
                env=env,
                check=check,
                capture_output=capture,
                text=True,
            )

        def request(port, method="GET", path="/", data=None, host="localhost"):
            body = json.dumps(data).encode() if data is not None else None
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}{path}",
                data=body,
                method=method,
                headers={"Host": host, "Content-Type": "application/json"},
            )
            try:
                response = urllib.request.urlopen(req, timeout=5)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                return response.status, json.load(response)

        try:
            run("config", "--quiet")
            run("build")
            run("up", "-d", "--no-build")
            port = (
                run("port", "web", "8000", capture=True)
                .stdout.strip()
                .rsplit(":", 1)[-1]
            )
            deadline = time.monotonic() + 45
            while True:
                try:
                    assert request(port)[0] == 200
                    break
                except (OSError, AssertionError):
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.5)
            assert request(port, host="disallowed.example")[0] == 400
            assert request(port, path="/admin")[0] == 404
            status, error = request(port, path="/api/school/students")
            assert (
                status == 500 and "detail" not in error
            )  # No startup migration or debug traceback.
            run(
                "exec",
                "-T",
                "web",
                "/app/.venv/bin/python",
                "-m",
                "rusjango",
                "migrate",
            )
            status, student = request(
                port, "POST", "/api/school/students", {"name": "Sara"}
            )
            assert status == 200 and isinstance(student["id"], int)
            assert request(port, path="/api/school/students")[1] == [student]
            run(
                "exec",
                "-T",
                "web",
                "/app/.venv/bin/python",
                "-c",
                "import os; assert os.geteuid() == 10001",
            )
            run(
                "exec",
                "-T",
                "web",
                "/app/.venv/bin/python",
                "-c",
                "from docker_app import app; from rusjango.admin import AdminIdentity; assert app.admin_site.catalog(identity=AdminIdentity('staff', frozenset({'admin:school.student:view'})))[0]['label'] == 'school.student'",
            )
            run("restart", "web")
            port = (
                run("port", "web", "8000", capture=True)
                .stdout.strip()
                .rsplit(":", 1)[-1]
            )
            deadline = time.monotonic() + 30
            while True:
                try:
                    assert request(port, path="/api/school/students")[1] == [student]
                    break
                except (OSError, AssertionError):
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.5)
            print(
                "Docker: nonroot runtime, production hosts/errors, explicit migration, CRUD, and persistent volume passed"
            )
        except BaseException:
            run("logs", "--no-color", check=False)
            raise
        finally:
            run("down", "--volumes", check=False)
            image = project_name + "-web"
            exists = subprocess.run(
                ["docker", "image", "inspect", image],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if exists.returncode == 0:
                subprocess.run(["docker", "image", "rm", image], check=False)


if __name__ == "__main__":
    main()
