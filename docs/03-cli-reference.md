# CLI Reference

The `rusjango` binary is a Rust-compiled CLI that scaffolds projects, manages apps, and drives the development server. All commands must be run from inside (or below) a directory that contains a `pyproject.toml` with a `[tool.rusjango]` section — except `rusjango new`, which creates that file for you.

---

## Project detection

Every command that operates on an existing project (dev, add, remove, migrate) walks up the directory tree from the current working directory until it finds a `pyproject.toml` containing `[tool.rusjango]`. If none is found, the command exits with an error:

```
No Rusjango project found (missing [tool.rusjango] in pyproject.toml)
```

---

## `rusjango new <name>`

Creates a new minimal Rusjango project in a subdirectory named `<name>`.

```
rusjango new <name> [--directory <path>]
```

### Options

| Flag | Description | Default |
|---|---|---|
| `--directory <path>`, `-d <path>` | Parent directory for the new project | Current directory |

The project is always placed at `<directory>/<name>`. If the directory already exists the command exits with an error.

### Name rules

Project names may contain letters, numbers, hyphens (`-`), and underscores (`_`). The name must not be empty.

### Generated files

**`main.py`**

```python
from rusjango import Rusjango

app = Rusjango(settings="settings.py")


@app.get("/")
async def home():
    return {"message": "Hello Rusjango"}


app.load_installed_apps()
```

**`settings.py`**

```python
APP_NAME = "<name>"
DEBUG = True
SECRET_KEY = "<random-50-char-secret>"
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
```

The `SECRET_KEY` is randomly generated at project creation time using a 50-character string drawn from letters, digits, and the symbols `!@#$%^&*(-_=+)`.

**`pyproject.toml`**

```toml
[project]
name = "<name>"
version = "0.1.0"
dependencies = [
    "rusjango",
]

[tool.rusjango]
settings = "settings.py"
app = "main:app"
```

The `[tool.rusjango]` section is what the CLI uses to detect the project root and resolve the ASGI app entry point.

### Post-creation steps

```bash
cd <name>
uv sync
rusjango dev
```

---

## `rusjango dev`

Starts the development server with uvicorn and auto-reload.

```
rusjango dev [--host <host>] [--port <port>] [--no-reload]
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--host <host>` | `127.0.0.1` | Address to bind |
| `--port <port>` | `8000` | Port to bind |
| `--no-reload` | *(reload on)* | Disable uvicorn auto-reload |

### How it works

1. The CLI locates the project root (see [Project detection](#project-detection)).
2. It runs `uv run python -m rusjango._dev --host <host> --port <port> [--no-reload]`.
3. `rusjango._dev` reads `[tool.rusjango] app` from `pyproject.toml` (defaults to `"main:app"`) and calls `uvicorn.run()` with that import string.
4. If `uv` is not available, the CLI falls back to invoking `python` directly.

When reload is enabled, uvicorn watches the entire project root directory for changes.

---

## `rusjango add app <name>`

Creates a new application package under `apps/<name>/` and registers it in `settings.py`.

```
rusjango add app <name>
```

### Name rules

| Rule | Detail |
|---|---|
| Allowed characters | Letters (`a-z`, `A-Z`), digits (`0-9`), underscores (`_`) |
| First character | Must be a letter or underscore |
| Reserved names | `apps`, `rusjango` |

### What it creates

```
apps/
├── __init__.py          # created if not present: "# Rusjango applications"
└── <name>/
    ├── __init__.py      # "# <name> application"
    └── api.py
```

**`apps/<name>/api.py`**

```python
from rusjango import Router

router = Router()


@router.get("/students")
async def list_students():
    return [{"name": "Ali"}, {"name": "Sara"}]
```

### Settings changes

`apps.<name>` is appended to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    "apps.<name>",
]
```

### `main.py` changes

If `main.py` does not already contain `app.load_installed_apps()`, the following lines are appended:

```python
# Load routers from INSTALLED_APPS
app.load_installed_apps()
```

### Route prefix

All routes defined in `apps/<name>/api.py` are automatically mounted at `/api/<name>/`. For example, a router route `@router.get("/students")` becomes accessible at `/api/<name>/students`.

---

## `rusjango remove app <name>`

Removes an application package and unregisters it from `settings.py`.

```
rusjango remove app <name> [--yes]
```

### Options

| Flag | Description |
|---|---|
| `--yes`, `-y` | Skip the confirmation prompt |

### What happens

1. Prompts for confirmation (unless `--yes`):
   ```
   This will remove the '<name>' app and unregister it from settings.py.
   Do you want to continue? [y/N]
   ```
2. Removes `"apps.<name>"` from `INSTALLED_APPS` in `settings.py`. If `INSTALLED_APPS` becomes empty, it is collapsed back to `INSTALLED_APPS = []`.
3. Deletes the `apps/<name>/` directory and all its contents.
4. If no `apps.*` entries remain in `settings.py`, removes the `app.load_installed_apps()` call (and its preceding comment) from `main.py`.

---

## `rusjango add orm`

Enables the async ORM with SQLite as the default backend.

```
rusjango add orm
```

This command is idempotent: if `DATABASE` is already configured (not `None`), it prints a notice and exits without changes.

### Changes to `settings.py`

Replaces `DATABASE = None` with:

```python
DATABASE = {
    "ENGINE": "sqlite",
    "NAME": "db.sqlite3",
    "ASYNC": True,
}
```

### Creates `migrations/` directory

An empty `migrations/.gitkeep` is written so the directory is tracked by git.

### Changes to `pyproject.toml`

Adds `aiosqlite>=0.20` to the `dependencies` list:

```toml
dependencies = [
    "aiosqlite>=0.20",
    "rusjango",
]
```

### Changes to existing apps

For every app listed in `INSTALLED_APPS`, the command checks `apps/<name>/`:

| File | Action |
|---|---|
| `models.py` | Created from template if not present |
| `schemas.py` | Created from template if not present |
| `api.py` | Upgraded to ORM version if it does not already import from `.models` |

**`apps/<name>/models.py`** (template):

```python
from rusjango.orm import Integer, Model, String


class Student(Model):
    id = Integer(primary_key=True)
    name = String(max_length=100)
    age = Integer(nullable=True)
```

**`apps/<name>/schemas.py`** (template):

```python
from rusjango.schema import Schema


class StudentCreate(Schema):
    name: str
    age: int


class StudentOut(Schema):
    id: int
    name: str
    age: int
```

**`apps/<name>/api.py`** (ORM-upgraded template):

```python
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
```

### Next steps

```bash
rusjango migrate   # create tables
rusjango dev       # start the server
```

---

## `rusjango remove orm`

Disables the ORM by setting `DATABASE = None`. Model files and `migrations/` are left intact.

```
rusjango remove orm [--yes]
```

### Options

| Flag | Description |
|---|---|
| `--yes`, `-y` | Skip the confirmation prompt |

### What happens

1. Prompts for confirmation (unless `--yes`):
   ```
   This will disable ORM and set DATABASE = None.
   Model files and migrations/ will be kept.
   Continue? [y/N]
   ```
2. Replaces the `DATABASE = { ... }` block in `settings.py` with `DATABASE = None` using a multiline regex.
3. Does **not** touch `models.py`, `schemas.py`, `api.py`, or `migrations/`.

---

## `rusjango migrate`

Creates database tables for all registered models.

```
rusjango migrate
```

### How it works

1. Runs `uv run python -m rusjango._migrate` from the project root (falls back to `python -m rusjango._migrate` if `uv` is unavailable).
2. `_migrate` reads `settings.py` and reads `DATABASE`. If `DATABASE` is `None`, it exits with an error.
3. Calls `configure_db(DATABASE)` to set the connection config.
4. Imports `<app>.models` for every entry in `INSTALLED_APPS` so that model classes are registered.
5. Calls `Model.create_table(if_not_exists=True)` for every registered model, which emits:
   ```sql
   CREATE TABLE IF NOT EXISTS "<table_name>" (...)
   ```
6. Prints `Migrations applied (tables created/verified).`

This command is safe to run multiple times — `CREATE TABLE IF NOT EXISTS` means it will not fail or duplicate data if the table already exists.

---

## Planned commands (not yet implemented)

The following subcommands are planned for future releases:

| Command | Description |
|---|---|
| `rusjango add admin` / `remove admin` | Admin panel scaffolding |
| `rusjango add auth` / `remove auth` | Authentication (JWT / session) |
| `rusjango add ai` / `remove ai` | AI integration helpers |
| `rusjango add worker` / `remove worker` | Background task queue |
| `rusjango add docker` / `remove docker` | Dockerfile and compose scaffolding |
| `rusjango add tests` / `remove tests` | Test suite scaffolding |
| `rusjango add payments` / `remove payments` | Payments integration |

These correspond to the `AUTH`, `ADMIN`, `AI`, `WORKER`, and `PAYMENTS` placeholder keys already present in the generated `settings.py`.
