# Rusjango — Getting Started

---

## Prerequisites

| Tool | Minimum version | Install |
|---|---|---|
| **Rust** | stable (1.75+) | https://rustup.rs |
| **uv** | 0.4+ | https://docs.astral.sh/uv |
| **Python** | 3.10 | bundled by uv, or https://python.org |

Rust is required to compile the CLI binary and the PyO3 core extension. uv manages the Python workspace, virtual environments, and package installs. Python 3.10 is the minimum because the codebase uses `match`-style type unions (`str | None`) and `tomllib` (stdlib in 3.11, backported via the standard `tomllib` module).

---

## Repository Setup

Clone the monorepo and bootstrap the Python workspace, then build the Rust extension and the CLI binary:

```bash
git clone <repo-url>
cd rusjango

# Install Python dependencies and set up the virtual environment
uv sync

# Build the PyO3 Rust extension and install it into the venv
uv run maturin develop -m python/rusjango/pyproject.toml

# Build the rusjango CLI binary
cargo build -p rusjango-cli
```

After `cargo build`, the binary is at `target/debug/rusjango` (Windows: `target\debug\rusjango.exe`). Add `target/debug` to your `PATH` or use `cargo run -p rusjango-cli --` as a prefix for any CLI command during development.

> **What `maturin develop` does:** It compiles `crates/rusjango-core` into a platform-specific extension (`_core.pyd` on Windows, `_core.so` on Linux/macOS) and copies it into `python/rusjango/src/rusjango/`. The Python package then imports it as `rusjango._core`. If the build is skipped, the import is silently ignored (see `__init__.py`) so the framework still works — you just lose the Rust-side version string.

---

## Create Your First Project

```bash
cargo run -p rusjango-cli -- new hello
cd hello
uv sync
rusjango dev
```

Then open http://127.0.0.1:8000 — you should see:

```json
{"message": "Hello Rusjango"}
```

The scaffolded project contains exactly four files:

```
hello/
├── main.py          # App instance + routes
├── settings.py      # All configuration (mostly None to start)
└── pyproject.toml   # Project metadata + [tool.rusjango] config
```

`main.py` out of the box:

```python
from rusjango import Rusjango

app = Rusjango(settings="settings.py")

@app.get("/")
async def home():
    return {"message": "Hello Rusjango"}

app.load_installed_apps()
```

`[tool.rusjango]` in `pyproject.toml` tells the CLI and dev server where to find the app:

```toml
[tool.rusjango]
settings = "settings.py"
app = "main:app"
```

`rusjango dev` reads this, `os.chdir`s to the project root, then starts:

```
Rusjango running at http://127.0.0.1:8000
  Auto-reload enabled
```

Auto-reload watches the project root for file changes and restarts uvicorn automatically. Pass `--no-reload` to disable it.

---

## Add an App

Apps are the primary way to organise code. Each app lives in `apps/<name>/` and exposes a `router` that gets mounted automatically under `/api/<name>/`.

```bash
rusjango add app school
```

This command:
1. Creates `apps/school/` with `__init__.py` and `api.py`.
2. Adds `"apps.school"` to `INSTALLED_APPS` in `settings.py`.
3. Ensures `app.load_installed_apps()` is present in `main.py`.

Resulting structure:

```
hello/
├── apps/
│   ├── __init__.py
│   └── school/
│       ├── __init__.py
│       └── api.py           # Router + handlers for this app
├── main.py
├── settings.py
└── pyproject.toml
```

`apps/school/api.py` generated content:

```python
from rusjango import Router

router = Router()

@router.get("/students")
async def list_students():
    return [{"name": "Ali"}, {"name": "Sara"}]
```

After `rusjango dev`, that endpoint is live at `GET /api/school/students`.

You can add multiple apps — `rusjango add app payments`, `rusjango add app auth` — and each gets its own package and route prefix. `load_installed_apps()` in `main.py` mounts them all at startup.

---

## Add the ORM

The ORM is disabled by default (`DATABASE = None` in `settings.py`). Enable it with:

```bash
rusjango add orm
```

This command:
1. Replaces `DATABASE = None` with a SQLite configuration block in `settings.py`.
2. Creates a `migrations/` directory.
3. Adds `aiosqlite` to `pyproject.toml` dependencies.
4. For every app already in `INSTALLED_APPS`, generates `models.py`, `schemas.py`, and upgrades `api.py` with ORM-wired routes (only if those files don't already exist).

```bash
rusjango migrate   # CREATE TABLE IF NOT EXISTS for every Model subclass
rusjango dev       # start server
```

The generated `apps/school/models.py`:

```python
from rusjango.orm import Integer, Model, String

class Student(Model):
    id = Integer(primary_key=True)
    name = String(max_length=100)
    age = Integer(nullable=True)
```

The generated `apps/school/schemas.py`:

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

The upgraded `apps/school/api.py`:

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

Test with curl:

```bash
curl -s http://127.0.0.1:8000/api/school/students
# []

curl -s -X POST http://127.0.0.1:8000/api/school/students \
     -H "Content-Type: application/json" \
     -d '{"name": "Ali", "age": 20}'
# {"id": 1, "name": "Ali", "age": 20}

curl -s http://127.0.0.1:8000/api/school/students
# [{"id": 1, "name": "Ali", "age": 20}]
```

### PostgreSQL instead of SQLite

Install the optional extra and update `settings.py` manually:

```bash
uv add "rusjango[postgres]"
```

```python
# settings.py
DATABASE = {
    "ENGINE": "postgresql",
    "URL": "postgresql://user:pass@localhost/mydb",
}
```

No other code changes needed — the ORM uses parameterised queries in both engines.

### QuerySet API

```python
# All records
students = await Student.all()

# Filtered
adults = await Student.filter(age__gte=18).all()

# Single record — raises DoesNotExist if not found
student = await Student.get(id=1)

# Chained filters
result = await Student.filter(age__gte=18).filter(name="Ali").first()

# Update
await Student.filter(id=1).update(name="Babar")

# Delete
await Student.filter(id=1).delete()
```

Supported lookup suffixes: `exact` (default), `gte`, `lte`, `gt`, `lt`.

---

## Run the Tests

Tests live in `python/rusjango/tests/`. Run them from the workspace root:

```bash
cd python/rusjango
uv run pytest tests/ -v
```

The test suite covers:

| File | What it tests |
|---|---|
| `test_import.py` | Package imports, `__version__`, optional `_core` extension |
| `test_asgi.py` | Route matching, path params, query params, 404 behaviour, body parsing |
| `test_apps.py` | `load_installed_apps`, router mounting, prefix handling |
| `test_config.py` | `find_project_root`, `load_rusjango_config` |
| `test_orm.py` | Model CRUD, QuerySet filters, schema round-trips (using in-memory SQLite) |

`conftest.py` provides `call_asgi(app, method, path, query, body)` — a helper that drives the ASGI app directly without a network socket, returning `(status_code, json_body)`.

To run a single test file:

```bash
uv run pytest tests/test_asgi.py -v
```

To run tests with output on failure:

```bash
uv run pytest tests/ -v --tb=short
```

---

## Environment Variables

| Variable | Purpose | When needed |
|---|---|---|
| `PYTHONPATH` | Adds `python/rusjango/src` to the module search path | When running `python` directly outside `uv run` (e.g., in `rusjango migrate`'s fallback path — the CLI sets this automatically when it can find the monorepo's `src` directory) |
| `UV_LINK_MODE` | Controls how uv links packages into the venv (`copy`, `hardlink`, `symlink`) | Only on filesystems that don't support hardlinks (some Docker mounts, network drives); set to `copy` to avoid install errors |
| `RUST_LOG` | Controls tracing output from the CLI (e.g., `RUST_LOG=debug`) | Only needed when debugging CLI internals |

---

## Windows-Specific Notes

- The compiled Rust extension is named `_core.pyd` on Windows (`.so` on Linux/macOS). Both are imported identically as `rusjango._core` — Python handles the platform difference transparently.
- The debug PDB file (`rusjango_core.pdb`) appears alongside `_core.pyd` after a debug build. It is safe to ignore and is excluded from release wheels.
- If `cargo build` reports link errors on Windows, ensure the MSVC build tools are installed (`rustup target add x86_64-pc-windows-msvc` and Visual Studio Build Tools with the C++ workload).
- Path separators in `PYTHONPATH` on Windows use `;` as the delimiter, but `uv run` handles this automatically when it constructs the environment.
- `rusjango dev` calls `uv run` as a subprocess, which inherits the current terminal's environment. If `uv` is installed via the official installer, it is on `PATH` in PowerShell and cmd but may not be in Git Bash — run from PowerShell or add `uv` to your Git Bash PATH manually.
