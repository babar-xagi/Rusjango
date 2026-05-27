"""Development server (uvicorn)."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path
from typing import Any

from rusjango.config import find_project_root, load_rusjango_config


def import_app(app_path: str) -> Any:
    """Import ``module:attr`` ASGI application."""
    module_name, sep, attr = app_path.partition(":")
    if not sep:
        msg = f"Invalid app path {app_path!r}; expected module:app"
        raise ValueError(msg)
    module = importlib.import_module(module_name)
    return getattr(module, attr)


def run_dev(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True,
    project_root: Path | None = None,
) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        msg = "uvicorn is required. Install with: pip install 'rusjango[server]' or uv add uvicorn"
        raise SystemExit(msg) from exc

    root = project_root or find_project_root()
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    config = load_rusjango_config(root)
    app_path = config.get("app", "main:app")

    # Uvicorn requires an import string (e.g. "main:app") when reload is enabled.
    if not reload:
        import_app(app_path)

    print(f"Rusjango running at http://{host}:{port}")
    if reload:
        print("  Auto-reload enabled")
    uvicorn.run(
        app_path,
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[str(root)] if reload else None,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rusjango development server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-reload", action="store_true")
    args = parser.parse_args(argv)
    run_dev(host=args.host, port=args.port, reload=not args.no_reload)


if __name__ == "__main__":
    main()
