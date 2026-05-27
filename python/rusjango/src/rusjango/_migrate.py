"""Apply database migrations (create tables from registered models)."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from rusjango.config import find_project_root, load_rusjango_config
from rusjango.orm.connection import close_db, configure_db, init_db
from rusjango.settings import load_settings


def _load_models(project_root: Path, installed_apps: list[str]) -> None:
    sys.path.insert(0, str(project_root))
    for dotted in installed_apps:
        try:
            importlib.import_module(f"{dotted}.models")
        except ModuleNotFoundError:
            pass


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rusjango migrate")
    parser.parse_args(argv)

    root = find_project_root()
    config = load_rusjango_config(root)
    settings_path = root / config.get("settings", "settings.py")
    settings = load_settings(settings_path)

    database = settings.get("DATABASE")
    if not database:
        print("DATABASE is not configured. Run `rusjango add orm` first.")
        raise SystemExit(1)

    configure_db(database)
    _load_models(root, settings.get("INSTALLED_APPS") or [])

    import asyncio

    async def run() -> None:
        await init_db()
        await close_db()

    asyncio.run(run())
    print("Migrations applied (tables created/verified).")


if __name__ == "__main__":
    main()
