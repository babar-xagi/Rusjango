"""Runnable admin scaffolds and per-app discovery through both CLIs."""

import subprocess
import sys


def test_admin_scaffold_loads_and_preserves_no_http_exposure(command, tmp_path):
    command("new", "sample")
    root = tmp_path / "sample"
    command("add", "app", "school", cwd=root)
    command("add", "orm", cwd=root)
    command("add", "admin", cwd=root)
    settings = root / "settings.py"
    settings.write_text(
        settings.read_text().replace(
            "ADMIN = None", 'ADMIN = {"FACTORY": "admin:create_site"}'
        )
    )
    (root / "apps/school/admin.py").write_text("""from .models import Student
def register(site):
    site.register(Student, list_display=("id", "name"), detail_fields=("id", "name", "age"))
""")
    command("migrate", cwd=root)
    script = """import asyncio
from main import app
from rusjango.admin import AdminIdentity
from rusjango.orm import close_db
site = app.admin_site
identity = AdminIdentity("staff", frozenset({"admin:school.student:view"}))
assert site.catalog(identity=identity)[0]["label"] == "school.student"
assert app.load_admin() is site
async def check():
    try:
        assert (await site.list("school.student", identity=identity))["items"] == []
        messages=[]
        async def receive(): return {"type":"http.request","body":b"","more_body":False}
        async def send(message): messages.append(message)
        await app({"type":"http","method":"GET","path":"/admin","query_string":b"","headers":[]},receive,send)
        assert messages[0]["status"] == 404
    finally:
        await close_db()
asyncio.run(check())
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env=command.env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    original = (root / "admin.py").read_text()
    command("remove", "admin", "--yes", cwd=root)
    assert not (root / "admin.py").exists()
    assert (root / "apps/school/admin.py").exists()
    assert 'ADMIN = {"FACTORY"' in settings.read_text()
    command("add", "admin", cwd=root)
    assert (root / "admin.py").read_text() == original
