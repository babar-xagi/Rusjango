"""Full Rusjango CLI — works out of the box after `pip install rusjango`.

All commands are implemented in pure Python so users never need the
separate Rust binary.  The Rust binary (cli/) is faster and used in
development, but both expose the same surface.
"""

from __future__ import annotations

import argparse
import os
import re
import secrets
import shutil
import string
import subprocess
import sys
from pathlib import Path
from typing import Any

# ── Embedded templates ────────────────────────────────────────────────────────

_MAIN_PY = """\
from rusjango import Rusjango

app = Rusjango(settings="settings.py")


@app.get("/")
async def home():
    return {"message": "Hello Rusjango"}


app.load_installed_apps()
"""

_SETTINGS_PY = """\
APP_NAME = "{name}"
DEBUG = True
SECRET_KEY = "{secret_key}"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = []

MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",
]

DATABASE = None
AUTH = None
ADMIN = None
AI = None
WORKER = None
PAYMENTS = None
"""

_PYPROJECT_TOML = """\
[project]
name = "{name}"
version = "0.1.0"
dependencies = [
    "rusjango",
]

[tool.rusjango]
settings = "settings.py"
app = "main:app"
"""

_APP_INIT = "# {name} app\n"

_APP_API = """\
from rusjango import Router

router = Router()


@router.get("/students")
async def list_students():
    return [{"name": "Ali"}, {"name": "Sara"}]
"""

_APP_API_ORM = """\
from rusjango import Router

from .models import Student
from .schemas import StudentCreate, StudentOut

router = Router()


@router.get("/students")
async def list_students():
    students = await Student.all()
    return [StudentOut.from_dict(s.to_dict()).dict() for s in students]


@router.post("/students")
async def create_student(data: StudentCreate):
    student = await Student.create(name=data.name, age=data.age)
    return StudentOut.from_dict(student.to_dict()).dict()
"""

_MODELS_PY = """\
from rusjango.orm import Integer, Model, String


class Student(Model):
    id = Integer(primary_key=True)
    name = String(max_length=100)
    age = Integer(nullable=True)
"""

_SCHEMAS_PY = """\
from rusjango.schema import Schema


class StudentCreate(Schema):
    name: str
    age: int


class StudentOut(Schema):
    id: int
    name: str
    age: int
"""

_DATABASE_BLOCK = """\
DATABASE = {
    "ENGINE": "sqlite",
    "NAME": "db.sqlite3",
    "ASYNC": True,
}"""

# ── Internal helpers ──────────────────────────────────────────────────────────


def _generate_secret_key() -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return "".join(secrets.choice(alphabet) for _ in range(50))


def _find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file() and "[tool.rusjango]" in pyproject.read_text(
            encoding="utf-8"
        ):
            return directory
    raise FileNotFoundError(
        "No Rusjango project found. "
        "Run this command from inside a project directory "
        "(pyproject.toml must contain [tool.rusjango])."
    )


def _load_rusjango_config(root: Path) -> dict[str, Any]:
    import tomllib

    with (root / "pyproject.toml").open("rb") as f:
        data = tomllib.load(f)
    return data.get("tool", {}).get("rusjango", {})


def _add_installed_app(settings_path: Path, module: str) -> None:
    content = settings_path.read_text(encoding="utf-8")
    if f'"{module}"' in content:
        return  # already registered
    # Case 1: INSTALLED_APPS = []  (empty, single line)
    if re.search(r"(?m)^INSTALLED_APPS\s*=\s*\[\s*\]\s*$", content):
        content = re.sub(
            r"(?m)^(INSTALLED_APPS\s*=\s*)\[\s*\]\s*$",
            f'\\1[\n    "{module}",\n]',
            content,
        )
    # Case 2: INSTALLED_APPS = [\n  ...\n]  (multi-line)
    elif re.search(r"(?ms)^INSTALLED_APPS\s*=\s*\[.*?\n\]", content):
        content = re.sub(
            r"(?ms)^(INSTALLED_APPS\s*=\s*\[)(.*?)(\n\])",
            lambda m: m.group(1) + m.group(2) + f'    "{module}",\n' + m.group(3),
            content,
        )
    else:
        msg = f"Could not find INSTALLED_APPS in {settings_path}"
        raise ValueError(msg)
    settings_path.write_text(content, encoding="utf-8")


def _remove_installed_app(settings_path: Path, module: str) -> None:
    content = settings_path.read_text(encoding="utf-8")
    if f'"{module}"' not in content:
        raise ValueError(f"App {module!r} not found in INSTALLED_APPS")
    content = re.sub(rf'(?m)^\s*"{re.escape(module)}",?\s*\n', "", content)
    # Collapse back to [] if now empty
    content = re.sub(
        r"(?m)^INSTALLED_APPS\s*=\s*\[\s*\n\s*\]",
        "INSTALLED_APPS = []",
        content,
    )
    settings_path.write_text(content, encoding="utf-8")


def _ensure_load_apps(main_path: Path) -> None:
    content = main_path.read_text(encoding="utf-8")
    if "load_installed_apps()" in content:
        return
    content = content.rstrip() + (
        "\n\n\n# Load routers from INSTALLED_APPS\napp.load_installed_apps()\n"
    )
    main_path.write_text(content, encoding="utf-8")


def _list_installed_apps(settings_path: Path) -> list[str]:
    content = settings_path.read_text(encoding="utf-8")
    return re.findall(r'"apps\.([a-zA-Z0-9_]+)"', content)


def _confirm(prompt: str) -> bool:
    try:
        return input(f"{prompt} [y/N] ").strip().lower() in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


# ── Command implementations ───────────────────────────────────────────────────


def _cmd_new(args: argparse.Namespace) -> None:
    name: str = args.name
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        sys.exit(
            f"Error: invalid project name {name!r}. Use letters, digits, hyphens, underscores."
        )

    target = Path(args.directory) / name if args.directory else Path(name)
    if target.exists():
        sys.exit(f"Error: directory already exists: {target}")

    secret_key = _generate_secret_key()
    target.mkdir(parents=True)
    (target / "main.py").write_text(_MAIN_PY, encoding="utf-8")
    (target / "settings.py").write_text(
        _SETTINGS_PY.format(name=name, secret_key=secret_key), encoding="utf-8"
    )
    (target / "pyproject.toml").write_text(
        _PYPROJECT_TOML.format(name=name), encoding="utf-8"
    )

    print(f"Created Rusjango project: {target}")
    print()
    print(f"  cd {target}")
    print("  uv sync")
    print("  rusjango dev")


def _cmd_dev(args: argparse.Namespace) -> None:
    root = _find_project_root()
    config = _load_rusjango_config(root)
    app_path = config.get("app", "main:app")

    host: str = args.host
    port: int = args.port
    reload: bool = not args.no_reload

    print(f"Rusjango running at http://{host}:{port}")
    if reload:
        print("  Auto-reload enabled")

    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        app_path,
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        cmd.append("--reload")

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def _cmd_add_app(args: argparse.Namespace) -> None:
    name: str = args.name
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        sys.exit(
            f"Error: invalid app name {name!r}. Must start with a letter or underscore."
        )
    if name in ("apps", "rusjango"):
        sys.exit(f"Error: {name!r} is a reserved name.")

    root = _find_project_root()
    apps_root = root / "apps"
    app_dir = apps_root / name

    if app_dir.exists():
        sys.exit(f"Error: app already exists: {app_dir}")

    apps_root.mkdir(exist_ok=True)
    if not (apps_root / "__init__.py").exists():
        (apps_root / "__init__.py").write_text(
            "# Rusjango applications\n", encoding="utf-8"
        )

    app_dir.mkdir()
    (app_dir / "__init__.py").write_text(_APP_INIT.format(name=name), encoding="utf-8")
    (app_dir / "api.py").write_text(_APP_API, encoding="utf-8")

    module = f"apps.{name}"
    _add_installed_app(root / "settings.py", module)

    main_path = root / "main.py"
    if main_path.is_file():
        _ensure_load_apps(main_path)

    print(f"Added app '{name}'")
    print(f"  Package : apps/{name}/")
    print(f'  Register: INSTALLED_APPS += "{module}"')
    print(f"  Routes  : /api/{name}/... (see apps/{name}/api.py)")


def _cmd_remove_app(args: argparse.Namespace) -> None:
    name: str = args.name
    root = _find_project_root()
    app_dir = root / "apps" / name
    module = f"apps.{name}"

    if not app_dir.is_dir():
        sys.exit(f"Error: app directory not found: {app_dir}")

    if not args.yes:
        print(f"This will remove the '{name}' app and unregister it from settings.py.")
        if not _confirm("Do you want to continue?"):
            print("Aborted.")
            return

    _remove_installed_app(root / "settings.py", module)
    shutil.rmtree(app_dir)

    print(f"Removed app '{name}'")
    print(f"  Deleted      : apps/{name}/")
    print(f'  Unregistered : "{module}" from INSTALLED_APPS')


def _cmd_add_orm(args: argparse.Namespace) -> None:  # noqa: ARG001
    root = _find_project_root()
    settings_path = root / "settings.py"
    content = settings_path.read_text(encoding="utf-8")

    if "DATABASE = {" in content and "DATABASE = None" not in content:
        print("ORM already enabled (DATABASE is configured).")
        return

    if "DATABASE = None" not in content:
        sys.exit("Error: could not find DATABASE = None in settings.py")

    settings_path.write_text(
        content.replace("DATABASE = None", _DATABASE_BLOCK), encoding="utf-8"
    )

    # migrations/
    migrations = root / "migrations"
    migrations.mkdir(exist_ok=True)
    gitkeep = migrations / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")

    # Add aiosqlite dependency
    pyproject_path = root / "pyproject.toml"
    pp = pyproject_path.read_text(encoding="utf-8")
    if "aiosqlite" not in pp:
        pp = re.sub(
            r"(?m)^dependencies = \[",
            'dependencies = [\n    "aiosqlite>=0.20",',
            pp,
        )
        pyproject_path.write_text(pp, encoding="utf-8")

    # Add models.py / schemas.py to existing apps
    settings_path2 = root / "settings.py"
    for app_name in _list_installed_apps(settings_path2):
        app_dir = root / "apps" / app_name
        if not app_dir.is_dir():
            continue
        if not (app_dir / "models.py").exists():
            (app_dir / "models.py").write_text(_MODELS_PY, encoding="utf-8")
        if not (app_dir / "schemas.py").exists():
            (app_dir / "schemas.py").write_text(_SCHEMAS_PY, encoding="utf-8")
        api_path = app_dir / "api.py"
        if api_path.exists():
            if "from .models import" not in api_path.read_text(encoding="utf-8"):
                api_path.write_text(_APP_API_ORM, encoding="utf-8")

    print("ORM enabled.")
    print("  DATABASE configured (SQLite: db.sqlite3)")
    print("  migrations/ created")
    print("  models.py / schemas.py added to apps (where missing)")
    print("  api.py upgraded with ORM routes (where not already done)")
    print()
    print("Next steps:")
    print("  rusjango migrate   — create tables")
    print("  rusjango dev       — start server")


def _cmd_remove_orm(args: argparse.Namespace) -> None:
    root = _find_project_root()
    settings_path = root / "settings.py"
    content = settings_path.read_text(encoding="utf-8")

    if "DATABASE = {" not in content:
        print("ORM is not enabled (DATABASE is None).")
        return

    if not args.yes:
        print("This will disable ORM and set DATABASE = None.")
        print("Model files and migrations/ will be kept.")
        if not _confirm("Continue?"):
            print("Aborted.")
            return

    new_content = re.sub(r"(?ms)^DATABASE = \{.*?\}\s*$", "DATABASE = None", content)
    settings_path.write_text(new_content, encoding="utf-8")
    print("ORM disabled (DATABASE = None).")


def _cmd_migrate(args: argparse.Namespace) -> None:  # noqa: ARG001
    root = _find_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "rusjango._migrate"],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root)},
    )
    sys.exit(result.returncode)


# ── Argument parser ───────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rusjango",
        description="Rusjango — Rust-powered async Python web framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  rusjango new myapp\n"
            "  rusjango dev\n"
            "  rusjango add app school\n"
            "  rusjango add orm\n"
            "  rusjango migrate\n"
            "  rusjango remove app school\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── new ──────────────────────────────────────────────────────────────
    p = sub.add_parser("new", help="Create a new minimal Rusjango project")
    p.add_argument("name", help="Project name (letters, digits, hyphens, underscores)")
    p.add_argument(
        "-d",
        "--directory",
        default=None,
        metavar="DIR",
        help="Parent directory (default: current directory)",
    )
    p.set_defaults(func=_cmd_new)

    # ── dev ──────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "dev", help="Start the development server (uvicorn + auto-reload)"
    )
    p.add_argument("--host", default="127.0.0.1", metavar="HOST")
    p.add_argument("--port", type=int, default=8000, metavar="PORT")
    p.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    p.set_defaults(func=_cmd_dev)

    # ── add ──────────────────────────────────────────────────────────────
    p_add = sub.add_parser("add", help="Add a feature or app to the project")
    add_sub = p_add.add_subparsers(dest="target", metavar="<target>")
    add_sub.required = True

    p = add_sub.add_parser(
        "app", help="Scaffold apps/<name>/ and register in INSTALLED_APPS"
    )
    p.add_argument("name", help="App name (letters, digits, underscores)")
    p.set_defaults(func=_cmd_add_app)

    p = add_sub.add_parser("orm", help="Enable async ORM with SQLite (default)")
    p.set_defaults(func=_cmd_add_orm)

    # ── remove ───────────────────────────────────────────────────────────
    p_remove = sub.add_parser("remove", help="Remove a feature or app from the project")
    remove_sub = p_remove.add_subparsers(dest="target", metavar="<target>")
    remove_sub.required = True

    p = remove_sub.add_parser(
        "app", help="Remove apps/<name>/ (prompts for confirmation)"
    )
    p.add_argument("name", help="App name")
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    p.set_defaults(func=_cmd_remove_app)

    p = remove_sub.add_parser(
        "orm", help="Disable ORM — sets DATABASE = None, keeps files"
    )
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    p.set_defaults(func=_cmd_remove_orm)

    # ── migrate ──────────────────────────────────────────────────────────
    p = sub.add_parser("migrate", help="Create database tables from registered models")
    p.set_defaults(func=_cmd_migrate)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
