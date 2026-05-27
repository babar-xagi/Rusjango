"""INSTALLED_APPS mounting tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from rusjango import Router, Rusjango
from conftest import call_asgi


@pytest.mark.asyncio
async def test_include_router_prefix() -> None:
    main = Rusjango()
    sub = Router()

    @sub.get("/items")
    async def items():
        return {"items": [1]}

    main.include_router(sub, prefix="/api/shop")

    status, data = await call_asgi(main, path="/api/shop/items")
    assert status == 200
    assert data["items"] == [1]


@pytest.mark.asyncio
async def test_load_installed_apps_from_disk(tmp_path: Path) -> None:
    apps_dir = tmp_path / "apps" / "school"
    apps_dir.mkdir(parents=True)
    (tmp_path / "apps" / "__init__.py").write_text("", encoding="utf-8")
    (apps_dir / "__init__.py").write_text("", encoding="utf-8")
    (apps_dir / "api.py").write_text(
        "from rusjango import Router\n"
        "router = Router()\n\n"
        "@router.get('/students')\n"
        "async def list_students():\n"
        "    return [{'name': 'Ali'}]\n",
        encoding="utf-8",
    )
    (tmp_path / "settings.py").write_text(
        "DEBUG = True\nINSTALLED_APPS = ['apps.school']\nMIDDLEWARE = []\n",
        encoding="utf-8",
    )
    settings_file = tmp_path / "settings.py"
    (tmp_path / "main.py").write_text(
        "from rusjango import Rusjango\n"
        f"app = Rusjango(settings={settings_file.as_posix()!r})\n"
        "app.load_installed_apps()\n",
        encoding="utf-8",
    )

    sys.path.insert(0, str(tmp_path))
    try:
        import importlib

        importlib.invalidate_caches()
        main_mod = importlib.import_module("main")
        app: Rusjango = main_mod.app
        status, data = await call_asgi(app, path="/api/school/students")
    finally:
        sys.path.remove(str(tmp_path))
        for key in list(sys.modules):
            if key in ("main", "settings", "apps", "apps.school", "apps.school.api"):
                del sys.modules[key]

    assert status == 200
    assert data == [{"name": "Ali"}]


@pytest.mark.asyncio
async def test_two_apps_no_cross_contamination(tmp_path: Path) -> None:
    """Routes from app A must NOT appear under app B's prefix."""
    for app_name in ("alpha", "beta"):
        app_dir = tmp_path / "apps" / app_name
        app_dir.mkdir(parents=True)
        (tmp_path / "apps" / "__init__.py").write_text("", encoding="utf-8")
        (app_dir / "__init__.py").write_text("", encoding="utf-8")
        route = "/alpha-route" if app_name == "alpha" else "/beta-route"
        (app_dir / "api.py").write_text(
            "from rusjango import Router\n"
            f"router = Router()\n\n"
            f"@router.get('{route}')\n"
            f"async def handler():\n"
            f"    return {{'app': '{app_name}'}}\n",
            encoding="utf-8",
        )
    (tmp_path / "settings.py").write_text(
        "DEBUG = True\nINSTALLED_APPS = ['apps.alpha', 'apps.beta']\nMIDDLEWARE = []\n",
        encoding="utf-8",
    )
    settings_file = tmp_path / "settings.py"
    (tmp_path / "main.py").write_text(
        "from rusjango import Rusjango\n"
        f"app = Rusjango(settings={settings_file.as_posix()!r})\n"
        "app.load_installed_apps()\n",
        encoding="utf-8",
    )

    sys.path.insert(0, str(tmp_path))
    try:
        import importlib

        importlib.invalidate_caches()
        main_mod = importlib.import_module("main")
        app: Rusjango = main_mod.app

        # alpha route under alpha prefix — must work
        s1, d1 = await call_asgi(app, path="/api/alpha/alpha-route")
        # beta route under beta prefix — must work
        s2, d2 = await call_asgi(app, path="/api/beta/beta-route")
        # alpha route must NOT be reachable under beta prefix
        s3, _ = await call_asgi(app, path="/api/beta/alpha-route")
    finally:
        sys.path.remove(str(tmp_path))
        for key in list(sys.modules):
            if key.startswith(("main", "settings", "apps")):
                del sys.modules[key]

    assert s1 == 200
    assert d1 == {"app": "alpha"}
    assert s2 == 200
    assert d2 == {"app": "beta"}
    assert s3 == 404  # cross-contamination guard
