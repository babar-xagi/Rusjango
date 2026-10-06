"""Full Rusjango CLI — works out of the box after `pip install rusjango`.

All commands are implemented in pure Python so users never need the
separate Rust binary. The Rust binary (cli/) is also available for
development; both expose the same commands.
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import secrets
import shutil
import string
import subprocess
import sys
from pathlib import Path
from typing import Any

from rusjango.config import find_project_root, load_rusjango_config

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
requires-python = ">=3.11"
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
    age: int | None = None


class StudentOut(Schema):
    id: int
    name: str
    age: int | None
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
    return find_project_root(start)


def _load_rusjango_config(root: Path) -> dict[str, Any]:
    return load_rusjango_config(root)


def _add_installed_app(settings_path: Path, module: str) -> None:
    content = settings_path.read_text(encoding="utf-8")
    apps = _literal_setting(content, "INSTALLED_APPS")
    if not isinstance(apps, list) or not all(isinstance(item, str) for item in apps):
        raise ValueError("INSTALLED_APPS must be a literal list of strings")
    if module not in apps:
        apps.append(module)
        rendered = "[\n" + "".join(f"    {item!r},\n" for item in apps) + "]"
        settings_path.write_text(
            _replace_setting(content, "INSTALLED_APPS", rendered), encoding="utf-8"
        )


def _remove_installed_app(settings_path: Path, module: str) -> None:
    content = settings_path.read_text(encoding="utf-8")
    apps = _literal_setting(content, "INSTALLED_APPS")
    if not isinstance(apps, list) or module not in apps:
        raise ValueError(f"App {module!r} not found in INSTALLED_APPS")
    apps = [item for item in apps if item != module]
    rendered = (
        "[\n" + "".join(f"    {item!r},\n" for item in apps) + "]" if apps else "[]"
    )
    settings_path.write_text(
        _replace_setting(content, "INSTALLED_APPS", rendered), encoding="utf-8"
    )


def _setting_node(content: str, name: str) -> ast.expr:
    matches = [
        node.value
        for node in ast.parse(content).body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one top-level {name} assignment")
    return matches[0]


def _literal_setting(content: str, name: str) -> Any:
    try:
        return ast.literal_eval(_setting_node(content, name))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{name} must use a literal value for CLI editing") from exc


def _replace_setting(content: str, name: str, value: str) -> str:
    node = _setting_node(content, name)
    lines = content.splitlines(keepends=True)
    start = sum(len(line) for line in lines[: node.lineno - 1])
    start += len(lines[node.lineno - 1].encode()[: node.col_offset].decode())
    end = sum(len(line) for line in lines[: node.end_lineno - 1])
    end += len(lines[node.end_lineno - 1].encode()[: node.end_col_offset].decode())
    return content[:start] + value + content[end:]


def _project_settings(root: Path) -> Path:
    return root / _load_rusjango_config(root).get("settings", "settings.py")


def _database_setting(content: str) -> dict[str, Any] | None:
    value = _literal_setting(content, "DATABASE")
    if value is not None and not isinstance(value, dict):
        raise ValueError("DATABASE must be None or a literal dictionary")
    return value


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
    apps = _literal_setting(content, "INSTALLED_APPS")
    if not isinstance(apps, list) or not all(isinstance(item, str) for item in apps):
        raise ValueError("INSTALLED_APPS must be a literal list of strings")
    return [
        module.removeprefix("apps.")
        for module in apps
        if isinstance(module, str)
        and re.fullmatch(r"apps\.[a-zA-Z_][a-zA-Z0-9_]*", module)
    ]


def _scaffold_orm_app(app_dir: Path) -> None:
    for filename, template in [("models.py", _MODELS_PY), ("schemas.py", _SCHEMAS_PY)]:
        path = app_dir / filename
        if not path.exists():
            path.write_text(template, encoding="utf-8")
    api_path = app_dir / "api.py"
    if (
        api_path.exists()
        and api_path.read_text(encoding="utf-8").strip() == _APP_API.strip()
    ):
        api_path.write_text(_APP_API_ORM, encoding="utf-8")


def _validate_app_name(name: str) -> None:
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", name) or name in (
        "apps",
        "rusjango",
    ):
        raise ValueError(f"Invalid or reserved app name: {name!r}")


def _confirm(prompt: str) -> bool:
    try:
        return input(f"{prompt} [y/N] ").strip().lower() in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


# ── Command implementations ───────────────────────────────────────────────────


def _cmd_new(args: argparse.Namespace) -> None:
    name: str = args.name
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
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
    _validate_app_name(name)

    root = _find_project_root()
    apps_root = root / "apps"
    app_dir = apps_root / name

    if app_dir.exists():
        sys.exit(f"Error: app already exists: {app_dir}")

    settings_path = _project_settings(root)
    content = settings_path.read_text(encoding="utf-8")
    apps = _literal_setting(content, "INSTALLED_APPS")
    database = _database_setting(content)
    if not isinstance(apps, list) or not all(isinstance(item, str) for item in apps):
        raise ValueError("INSTALLED_APPS must be a literal list of strings")

    apps_root.mkdir(exist_ok=True)
    if not (apps_root / "__init__.py").exists():
        (apps_root / "__init__.py").write_text(
            "# Rusjango applications\n", encoding="utf-8"
        )

    app_dir.mkdir()
    (app_dir / "__init__.py").write_text(_APP_INIT.format(name=name), encoding="utf-8")
    (app_dir / "api.py").write_text(_APP_API, encoding="utf-8")

    module = f"apps.{name}"
    _add_installed_app(settings_path, module)
    if database:
        _scaffold_orm_app(app_dir)

    main_path = root / "main.py"
    if main_path.is_file():
        _ensure_load_apps(main_path)

    print(f"Added app '{name}'")
    print(f"  Package : apps/{name}/")
    print(f'  Register: INSTALLED_APPS += "{module}"')
    print(f"  Routes  : /api/{name}/... (see apps/{name}/api.py)")


def _cmd_remove_app(args: argparse.Namespace) -> None:
    name: str = args.name
    _validate_app_name(name)
    root = _find_project_root()
    app_dir = root / "apps" / name
    module = f"apps.{name}"
    if (
        (root / "apps").is_symlink()
        or app_dir.is_symlink()
        or app_dir.resolve().parent != (root / "apps").resolve()
    ):
        raise ValueError("Refusing to remove an app outside the apps directory")

    if not app_dir.is_dir():
        sys.exit(f"Error: app directory not found: {app_dir}")

    if not args.yes:
        print(f"This will remove the '{name}' app and unregister it from settings.py.")
        if not _confirm("Do you want to continue?"):
            print("Aborted.")
            return

    _remove_installed_app(_project_settings(root), module)
    shutil.rmtree(app_dir)

    print(f"Removed app '{name}'")
    print(f"  Deleted      : apps/{name}/")
    print(f'  Unregistered : "{module}" from INSTALLED_APPS')


def _cmd_add_orm(args: argparse.Namespace) -> None:  # noqa: ARG001
    root = _find_project_root()
    settings_path = _project_settings(root)
    content = settings_path.read_text(encoding="utf-8")
    apps = _list_installed_apps(settings_path)

    if _database_setting(content) is None:
        settings_path.write_text(
            _replace_setting(content, "DATABASE", _DATABASE_BLOCK.partition("= ")[2]),
            encoding="utf-8",
        )

    # migrations/
    migrations = root / "migrations"
    migrations.mkdir(exist_ok=True)
    gitkeep = migrations / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")

    # Add models.py / schemas.py to existing apps
    for app_name in apps:
        app_dir = root / "apps" / app_name
        if not app_dir.is_dir():
            continue
        _scaffold_orm_app(app_dir)

    print("ORM enabled.")
    print("  DATABASE configured (SQLite: db.sqlite3)")
    print("  migrations/ created")
    print("  models.py / schemas.py added to apps (where missing)")
    print("  Untouched starter APIs upgraded; custom APIs preserved")
    print()
    print("Next steps:")
    print("  rusjango migrate   — create tables")
    print("  rusjango dev       — start server")


def _cmd_remove_orm(args: argparse.Namespace) -> None:
    root = _find_project_root()
    settings_path = _project_settings(root)
    content = settings_path.read_text(encoding="utf-8")

    if _database_setting(content) is None:
        print("ORM is not enabled (DATABASE is None).")
        return

    if not args.yes:
        print("This will disable ORM and set DATABASE = None.")
        print("Model files and migrations/ will be kept.")
        if not _confirm("Continue?"):
            print("Aborted.")
            return

    new_content = _replace_setting(content, "DATABASE", "None")
    settings_path.write_text(new_content, encoding="utf-8")
    print("ORM disabled (DATABASE = None).")


def _cmd_migrate(args: argparse.Namespace) -> None:  # noqa: ARG001
    root = _find_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "rusjango._migrate"],
        cwd=root,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(root), os.environ.get("PYTHONPATH", "")]
            ),
        },
    )
    sys.exit(result.returncode)


def _cmd_add_feature(args: argparse.Namespace) -> None:
    from rusjango.scaffolding import add_feature

    changed = add_feature(_find_project_root(), args.target)
    print(f"{args.target} scaffold {'added' if changed else 'already tracked'}.")
    if args.target == "tests":
        print("Run: uv run --with pytest --with pytest-asyncio pytest tests")
    elif args.target == "docker":
        print("Set ALLOWED_HOSTS, then run: docker compose up --build")
    else:
        print(
            "Configure ADMIN = {'FACTORY': 'admin:create_site'} and register explicit model fields."
        )


def _cmd_remove_feature(args: argparse.Namespace) -> None:
    from rusjango.scaffolding import remove_feature

    if not args.yes and not _confirm(
        f"Remove unchanged generated {args.target} files?"
    ):
        print("Aborted.")
        return
    kept = remove_feature(_find_project_root(), args.target)
    print(f"{args.target} scaffold removed.")
    for name in kept:
        print(f"Preserved modified file: {name}")


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

    for target in ("docker", "tests", "admin"):
        p = add_sub.add_parser(
            target, help=f"Add {target} scaffolding without overwriting files"
        )
        p.set_defaults(func=_cmd_add_feature)

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

    for target in ("docker", "tests", "admin"):
        p = remove_sub.add_parser(
            target, help=f"Remove unchanged generated {target} files"
        )
        p.add_argument(
            "-y", "--yes", action="store_true", help="Skip confirmation prompt"
        )
        p.set_defaults(func=_cmd_remove_feature)

    # ── migrate ──────────────────────────────────────────────────────────
    p = sub.add_parser("migrate", help="Create database tables from registered models")
    p.set_defaults(func=_cmd_migrate)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (ValueError, OSError, SyntaxError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
