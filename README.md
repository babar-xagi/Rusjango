<div align="center">

# Rusjango

**Rust-powered async Python web framework**

*Start like Flask · Scale like Django · Perform like Rust · Build AI apps natively*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/Rust-stable-orange?logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-13%20passing-brightgreen)](#testing)
[![Phase](https://img.shields.io/badge/phase-3%20of%2010-blue)](#roadmap)

</div>

---

## What is Rusjango?

Rusjango is a modern Python web framework with a Rust core.
It is inspired by Django, FastAPI, Polars, and modern AI-native backend systems.

The core idea is simple:

> A developer starts with three files and grows into a full enterprise framework — without ever changing frameworks.

```bash
rusjango new myapp          # three files: main.py, settings.py, pyproject.toml
rusjango add app users      # add a feature
rusjango add orm            # add another feature
rusjango add auth           # add another feature
rusjango remove app users   # safely remove what you no longer need
```

**No bloat by default. Everything is opt-in.**

---

## Why Rusjango?

| Problem with existing tools | Rusjango solution |
|---|---|
| Django was built sync-first | Fully async from the ground up |
| New Django project has too many files | Three files: `main.py`, `settings.py`, `pyproject.toml` |
| Django ORM is not async-native | Custom async-first ORM |
| Django admin UI feels outdated | Modern React + Tailwind admin *(Phase 5)* |
| FastAPI has no built-in ORM or admin | Native ORM + admin built in |
| Python-only frameworks have performance limits | Rust-powered routing, middleware, serialization |
| No framework is AI-native | Native LLM/RAG/agent module *(Phase 9)* |
| Features pile up and can't be removed | Every feature is removable with `rusjango remove` |

---

## Features

### Available now (Phase 1–3)

- **Minimal project scaffold** — `rusjango new` creates exactly 3 files
- **Async HTTP routing** — `@app.get`, `@app.post`, `@app.put`, `@app.delete`
- **Path & query parameters** — auto type coercion (`int`, `float`, `bool`, `str`)
- **JSON request body** — parsed automatically, validated via `Schema`
- **Schema validation** — lightweight typed request/response objects
- **Middleware system** — composable ASGI middleware stack
- **Security middleware** — host validation + `X-Frame-Options` / `X-Content-Type-Options`
- **App system** — `rusjango add app <name>` scaffolds a self-contained app package
- **INSTALLED_APPS** — auto-discovery and route mounting under `/api/<app>/`
- **Per-app Router isolation** — each app owns its own route table, no cross-contamination
- **Async ORM** — Django-style model API, fully async
- **SQLite support** — via `aiosqlite`, zero config
- **PostgreSQL support** — via `asyncpg`
- **ORM filter lookups** — `exact`, `gte`, `lte`, `gt`, `lt`
- **Migrations** — `rusjango migrate` creates tables from registered models
- **Dev server** — uvicorn with auto-reload via `rusjango dev`
- **Rust CLI** — fast binary with rich help output

### Coming soon

| Feature | Phase |
|---|---|
| `rusjango add docker` | Phase 4 |
| `rusjango add tests` | Phase 4 |
| Full Schema validation (coercion, defaults, nested) | Phase 4 |
| Admin panel (React + Tailwind, auto CRUD) | Phase 5 |
| Auth system (JWT, sessions, argon2, roles) | Phase 6 |
| Auto API docs (OpenAPI) | Phase 7 |
| Background workers (Redis) | Phase 8 |
| AI/LLM native module (RAG, streaming, tool calls) | Phase 9 |
| Enterprise: audit logs, multi-tenancy, observability | Phase 10 |

---

## Quick Start

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Rust | stable | [rustup.rs](https://rustup.rs) |
| uv | latest | [docs.astral.sh/uv](https://docs.astral.sh/uv) |
| Python | 3.10+ | via uv or system |

### 1. Clone and build

```bash
git clone git@github.com:babar-xagi/Rusjango.git
cd Rusjango

# Install Python dependencies
uv sync

# Build the Rust extension (PyO3 / maturin)
uv run maturin develop -m python/rusjango/pyproject.toml

# Build the CLI binary
cargo build -p rusjango-cli
```

### 2. Create your first project

```bash
cargo run -p rusjango-cli -- new hello
cd hello
uv sync
cargo run -p rusjango-cli -- dev
```

Open **http://127.0.0.1:8000** — you should see:

```json
{ "message": "Hello Rusjango" }
```

> **After `cargo install`:** Once you run `cargo install --path cli` from the repo root, you can use `rusjango` directly instead of `cargo run -p rusjango-cli --`.

---

## Your First Project — Step by Step

### Step 1 — Create project

```bash
rusjango new hello
cd hello
```

Generated structure:

```
hello/
├── main.py
├── settings.py
└── pyproject.toml
```

`main.py`:
```python
from rusjango import Rusjango

app = Rusjango(settings="settings.py")

@app.get("/")
async def home():
    return {"message": "Hello Rusjango"}

app.load_installed_apps()
```

### Step 2 — Run the server

```bash
rusjango dev
```

```
Rusjango running at http://127.0.0.1:8000
  Auto-reload enabled
```

### Step 3 — Add an app

```bash
rusjango add app school
```

Creates `apps/school/` and registers it in `settings.py`:

```
hello/
├── main.py
├── settings.py
├── apps/
│   └── school/
│       ├── __init__.py
│       └── api.py          ← routes are at /api/school/...
└── pyproject.toml
```

`apps/school/api.py`:
```python
from rusjango import Router

router = Router()

@router.get("/students")
async def list_students():
    return [{"name": "Ali"}, {"name": "Sara"}]
```

### Step 4 — Add the ORM

```bash
rusjango add orm
rusjango migrate
```

Adds `models.py` and `schemas.py` to every app, creates `migrations/`, configures SQLite:

```python
# apps/school/models.py
from rusjango.orm import Model, Integer, String

class Student(Model):
    id = Integer(primary_key=True)
    name = String(max_length=100)
    age = Integer(nullable=True)
```

```python
# apps/school/api.py  (upgraded automatically)
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

### Step 5 — Remove what you don't need

```bash
rusjango remove app school
```

```
This will remove the 'school' app and unregister it from settings.py.
Do you want to continue? [y/N]
```

Safe by default. Always asks before deleting.

---

## API Reference

### Route decorators

```python
@app.get("/path")
@app.post("/path")
@app.put("/path/{id}")
@app.delete("/path/{id}")
```

### Path parameters

```python
@app.get("/students/{id}")
async def get_student(id: int):      # auto-cast to int
    return {"id": id}
```

### Query parameters

```python
@app.get("/students")
async def list_students(limit: int = 10, search: str = ""):
    ...
```

### Request body

```python
from rusjango import Schema

class StudentCreate(Schema):
    name: str
    age: int

@app.post("/students")
async def create_student(data: StudentCreate):
    return data.dict()
```

### HTTP exceptions

```python
from rusjango import HTTPException

@app.get("/admin")
async def admin():
    raise HTTPException(403, detail="Forbidden")
```

### Per-app Router

```python
# apps/school/api.py
from rusjango import Router

router = Router()   # always create a fresh instance per app

@router.get("/students")
async def list_students():
    return []
```

---

## ORM Reference

### Model definition

```python
from rusjango.orm import Model, Integer, String, Text, Boolean

class Post(Model):
    id      = Integer(primary_key=True)
    title   = String(max_length=200)
    body    = Text(nullable=True)
    active  = Boolean(default=True)
```

### CRUD

```python
# Create
post = await Post.create(title="Hello", body="World")

# Read
post = await Post.get(id=1)              # raises DoesNotExist if not found
posts = await Post.all()
posts = await Post.filter(active=True).all()

# Filter lookups: exact (default), gte, lte, gt, lt
posts = await Post.filter(id__gte=5).all()

# Update
await Post.filter(id=1).update(title="Updated")

# Delete
await Post.filter(id=1).delete()
```

### Database settings

```python
# settings.py — SQLite (default)
DATABASE = {
    "ENGINE": "sqlite",
    "NAME": "db.sqlite3",
    "ASYNC": True,
}

# PostgreSQL
DATABASE = {
    "ENGINE": "postgresql",
    "URL": "postgresql://user:pass@localhost:5432/mydb",
    "ASYNC": True,
}
```

---

## CLI Reference

| Command | Description |
|---|---|
| `rusjango new <name>` | Create a minimal 3-file project |
| `rusjango dev` | Start dev server (uvicorn + auto-reload) |
| `rusjango dev --host 0.0.0.0 --port 9000` | Custom host/port |
| `rusjango dev --no-reload` | Disable auto-reload |
| `rusjango add app <name>` | Scaffold `apps/<name>/` and register it |
| `rusjango remove app <name>` | Remove app (prompts for confirmation) |
| `rusjango remove app <name> --yes` | Remove without prompting |
| `rusjango add orm` | Enable async ORM (SQLite by default) |
| `rusjango remove orm` | Disable ORM, keep model files |
| `rusjango migrate` | Create database tables from models |

**Planned commands:**

| Command | Phase |
|---|---|
| `rusjango add admin` / `remove admin` | Phase 5 |
| `rusjango add auth` / `remove auth` | Phase 6 |
| `rusjango add docker` / `remove docker` | Phase 4 |
| `rusjango add tests` / `remove tests` | Phase 4 |
| `rusjango add worker` / `remove worker` | Phase 8 |
| `rusjango add ai` / `remove ai` | Phase 9 |
| `rusjango add payments` / `remove payments` | Phase 10 |

---

## Project Structure

```
Rusjango/
├── Cargo.toml                    # Rust workspace (core + CLI)
├── pyproject.toml                # uv workspace root
├── PROGRESS.md                   # Phase-by-phase build tracker
│
├── crates/rusjango-core/         # PyO3 Rust extension
│   └── src/
│       ├── lib.rs                # Python module entry point
│       └── router.rs             # Future: Rust-accelerated routing
│
├── cli/                          # rusjango binary (clap)
│   └── src/
│       ├── main.rs               # Command definitions
│       ├── new.rs                # rusjango new
│       ├── add.rs                # rusjango add app
│       ├── remove.rs             # rusjango remove app
│       ├── orm.rs                # rusjango add/remove orm + migrate
│       ├── dev.rs                # rusjango dev
│       ├── project.rs            # Template rendering, project root detection
│       └── settings.rs           # settings.py manipulation (regex-based)
│
├── python/rusjango/              # Python package (maturin)
│   ├── pyproject.toml
│   └── src/rusjango/
│       ├── __init__.py           # Public API: Rusjango, Router, Schema, HTTPException
│       ├── app.py                # Rusjango application class + route decorators
│       ├── routing.py            # Route compilation, param extraction, handler dispatch
│       ├── asgi.py               # ASGI helpers: read_body, send_json, send_error
│       ├── middleware.py         # Middleware stack builder
│       ├── security.py           # SecurityMiddleware
│       ├── schema.py             # Schema base class
│       ├── settings.py           # settings.py loader
│       ├── config.py             # pyproject.toml discovery
│       ├── apps.py               # INSTALLED_APPS loader + router mounting
│       ├── exceptions.py         # HTTPException, error envelope
│       ├── server.py             # Dev server (uvicorn)
│       └── orm/
│           ├── model.py          # Model metaclass + CRUD
│           ├── fields.py         # Integer, String, Text, Boolean
│           ├── query.py          # QuerySet (lazy, chainable)
│           ├── sql.py            # SQL generation (parameterized, injection-safe)
│           └── connection.py     # aiosqlite / asyncpg connection management
│
├── templates/                    # .tpl files for code generation
│   ├── project/                  # rusjango new templates
│   ├── app/                      # rusjango add app templates
│   └── orm/                      # rusjango add orm templates
│
├── examples/
│   └── hello/                    # Working example project (school app + ORM)
│
└── docs/                         # Documentation (14 files)
    ├── 00-overview.md
    ├── 01-architecture.md
    ├── 02-getting-started.md
    ├── 03-cli-reference.md
    ├── 04-api-design.md
    ├── 05-orm-guide.md
    ├── 06-settings-reference.md
    ├── 07-middleware.md
    ├── 08-schema-validation.md
    ├── 09-progress.md
    ├── 10-contributing.md
    └── internals/
        ├── rust-core.md
        ├── python-layer.md
        └── orm-internals.md
```

---

## Development Setup

```bash
# 1. Clone
git clone git@github.com:babar-xagi/Rusjango.git
cd Rusjango

# 2. Python deps
uv sync

# 3. Build Rust extension (PyO3 / maturin)
uv run maturin develop -m python/rusjango/pyproject.toml

# 4. Build CLI
cargo build -p rusjango-cli

# 5. Run tests
cd python/rusjango
uv run pytest tests/ -v
```

---

## Testing

```
tests/test_import.py        package version importable
tests/test_asgi.py          routing, path params, POST body, HTTPException (5 tests)
tests/test_apps.py          INSTALLED_APPS loading, multi-app router isolation (3 tests)
tests/test_config.py        pyproject.toml project root discovery
tests/test_orm.py           ORM CRUD, filters, update, delete — SQLite (3 tests)
```

```bash
cd python/rusjango
uv run pytest tests/ -v
# 13 passed in ~0.5s
```

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  Developer Layer (Python)                            │
│  @app.get("/")  |  class Student(Model)  |  Schema   │
├──────────────────────────────────────────────────────┤
│  Framework Layer (Python)                            │
│  routing · ASGI · middleware · ORM query builder     │
├──────────────────────────────────────────────────────┤
│  Core Layer (Rust — PyO3)                            │
│  routing acceleration · serialization · conn pool   │
│  (current: version stub + future expansion)          │
└──────────────────────────────────────────────────────┘
         ↑ served by uvicorn (ASGI 3.0)
```

**Python-Rust boundary rule:**
> Rust handles heavy batch operations — routing, serialization, connection pooling.
> Python handles business logic — models, handlers, middleware.

---

## Roadmap

| Phase | Goal | Status |
|---|---|---|
| 1 | CLI + minimal API framework | ✅ Complete |
| 2 | Add/Remove app system | ✅ Complete |
| 3 | Async ORM foundation | ✅ Complete |
| 4 | Schema validation + Docker + Tests scaffolding | 🚧 In progress |
| 5 | Admin panel MVP (React + Tailwind) | 📋 Planned |
| 6 | Auth system (JWT, sessions, argon2) | 📋 Planned |
| 7 | API docs + developer experience | 📋 Planned |
| 8 | Worker system (Redis background tasks) | 📋 Planned |
| 9 | AI/LLM native module (RAG, streaming) | 📋 Planned |
| 10 | Enterprise features (multi-tenancy, audit, metrics) | 📋 Planned |

See [`PROGRESS.md`](PROGRESS.md) for full details and [`docs/09-progress.md`](docs/09-progress.md) for per-phase file references.

---

## Documentation

All docs live in [`docs/`](docs/):

| File | What it covers |
|---|---|
| [`docs/00-overview.md`](docs/00-overview.md) | Project vision, problems solved, user types, tech stack |
| [`docs/01-architecture.md`](docs/01-architecture.md) | Monorepo layout, 3-layer arch, request lifecycle |
| [`docs/02-getting-started.md`](docs/02-getting-started.md) | Full setup guide from scratch |
| [`docs/03-cli-reference.md`](docs/03-cli-reference.md) | Every CLI command with options and examples |
| [`docs/04-api-design.md`](docs/04-api-design.md) | Routes, params, body, Schema, Router, middleware |
| [`docs/05-orm-guide.md`](docs/05-orm-guide.md) | Models, fields, CRUD, filters, migrations |
| [`docs/06-settings-reference.md`](docs/06-settings-reference.md) | Every settings key explained |
| [`docs/07-middleware.md`](docs/07-middleware.md) | Middleware system, custom middleware |
| [`docs/08-schema-validation.md`](docs/08-schema-validation.md) | Schema class, validation, limitations |
| [`docs/09-progress.md`](docs/09-progress.md) | Phase tracker with file references |
| [`docs/10-contributing.md`](docs/10-contributing.md) | How to add features, code style, PR checklist |
| [`docs/internals/rust-core.md`](docs/internals/rust-core.md) | PyO3, maturin, clap internals |
| [`docs/internals/python-layer.md`](docs/internals/python-layer.md) | ASGI, routing dispatch, settings isolation |
| [`docs/internals/orm-internals.md`](docs/internals/orm-internals.md) | Metaclass, SQL generation, connection lifecycle |

---

## Contributing

1. Read [`docs/10-contributing.md`](docs/10-contributing.md)
2. Set up the dev environment (see [Development Setup](#development-setup))
3. Run the test suite and make sure it passes
4. Open a pull request with a clear description

**Development rules:**
- Keep the default project tiny — never generate unnecessary files
- Every feature must be removable
- Every CLI command must update `settings.py` automatically
- Dangerous commands must ask for confirmation
- ORM must be async-first
- Rust speeds up internals — Python owns business logic
- Documentation is written alongside code, not after

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
<sub>Built with Python · Rust · PyO3 · maturin · clap · uvicorn · aiosqlite · asyncpg</sub>
</div>
