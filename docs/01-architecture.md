# Rusjango — Architecture

---

## Monorepo Layout

```
rusjango/
├── Cargo.toml                       # Rust workspace (members: core + CLI)
├── pyproject.toml                   # uv workspace root (members: python/rusjango, examples/hello)
├── crates/
│   └── rusjango-core/               # PyO3 Rust extension → rusjango._core
│       └── src/
│           ├── lib.rs               # #[pymodule] entry point
│           └── router.rs            # Placeholder; future routing acceleration
├── cli/
│   └── src/
│       ├── main.rs                  # clap CLI definition + dispatch
│       ├── new.rs                   # `rusjango new` — scaffold a project
│       ├── add.rs                   # `rusjango add app` — add an app package
│       ├── dev.rs                   # `rusjango dev` — start uvicorn via uv
│       ├── orm.rs                   # `rusjango add/remove orm`, `rusjango migrate`
│       ├── remove.rs                # `rusjango remove app`
│       ├── project.rs               # Shared: find_project_root, render_template, generate_secret_key
│       └── settings.rs              # Helpers: add_installed_app, ensure_main_loads_apps
├── python/rusjango/                 # Python package (built by maturin)
│   ├── pyproject.toml               # Package metadata + maturin config
│   ├── src/rusjango/                # Importable package
│   │   ├── __init__.py              # Public API: Rusjango, Router, Schema, HTTPException
│   │   ├── app.py                   # Rusjango class — ASGI callable, route decorators
│   │   ├── routing.py               # Route dataclass, compile_route, call_handler
│   │   ├── asgi.py                  # read_body, send_json, send_error, parse_json_body
│   │   ├── middleware.py            # build_middleware_stack, import_string, ASGIApp type
│   │   ├── security.py              # SecurityMiddleware — host validation, security headers
│   │   ├── schema.py                # Schema base class — dict ↔ typed object
│   │   ├── settings.py              # load_settings — import settings.py as a plain dict
│   │   ├── config.py                # find_project_root, load_rusjango_config ([tool.rusjango])
│   │   ├── apps.py                  # load_installed_apps — mount INSTALLED_APPS routers
│   │   ├── router.py                # Module-level router singleton (convenience import)
│   │   ├── exceptions.py            # HTTPException, error_envelope
│   │   ├── server.py                # run_dev — launch uvicorn with reload
│   │   ├── _dev.py                  # Entry point for `python -m rusjango._dev`
│   │   ├── _migrate.py              # Entry point for `python -m rusjango._migrate`
│   │   ├── _core.pyd / _core.so     # Compiled Rust extension (platform-specific)
│   │   ├── _core.pyi                # Type stubs for the Rust extension
│   │   └── orm/
│   │       ├── model.py             # Model metaclass, Model base class, registry
│   │       ├── fields.py            # Field types: Integer, String, Text, Boolean
│   │       ├── query.py             # QuerySet — async filter / all / get / update / delete
│   │       ├── sql.py               # SQL generation: CREATE TABLE, INSERT, SELECT, UPDATE, DELETE
│   │       └── connection.py        # Async connection pool (aiosqlite / asyncpg)
│   └── tests/                       # pytest suite
├── templates/
│   ├── project/                     # Templates for `rusjango new`
│   │   ├── main.py.tpl
│   │   ├── settings.py.tpl
│   │   └── pyproject.toml.tpl
│   ├── app/                         # Templates for `rusjango add app`
│   │   ├── __init__.py.tpl
│   │   └── api.py.tpl
│   └── orm/                         # Templates for `rusjango add orm`
│       ├── models.py.tpl
│       ├── schemas.py.tpl
│       └── api_with_orm.py.tpl
├── examples/
│   └── hello/                       # Runnable example project
└── docs/                            # This documentation
```

---

## Three-Layer Architecture

```
┌───────────────────────────────────────────┐
│  1. Developer layer  (Python)             │
│     @app.get("/")  async def home(): ...  │
│     class Student(Model): ...             │
│     class StudentCreate(Schema): ...      │
├───────────────────────────────────────────┤
│  2. Framework layer  (Python)             │
│     Routing · ASGI · Middleware           │
│     ORM query builder · Settings          │
├───────────────────────────────────────────┤
│  3. Core layer  (Rust)                    │
│     rusjango._core (PyO3 extension)       │
│     Future: routing, serialization,       │
│     connection pooling                    │
└───────────────────────────────────────────┘
```

### Layer 1 — Developer layer (Python)

What application developers write: route handlers decorated with `@app.get(...)`, model classes that extend `Model`, schema classes that extend `Schema`, and a `settings.py` file with uppercase constants. No generated boilerplate needs to be understood or maintained.

### Layer 2 — Framework layer (Python)

Everything the developer layer calls into: `Rusjango.__call__` is the ASGI entry point; `routing.py` compiles path patterns into regexes and dispatches requests; `middleware.py` wraps the core handler in a configurable stack; `apps.py` mounts each installed app's router under `/api/<name>`; the ORM translates Python method calls into parameterised SQL and runs them through an async connection.

### Layer 3 — Core layer (Rust)

`crates/rusjango-core` is compiled by maturin into `rusjango._core`. Today it exposes `__version__` and a stub `route_count()`. The architecture is intentional: the boundary is already established so routing acceleration, JSON serialisation, and connection pooling can be moved to Rust incrementally without any changes to the developer API.

**Boundary rule:** Rust handles heavy, stateless, batch operations (route matching at scale, bulk serialisation). Python handles business logic, database access, and anything that benefits from dynamic typing or ecosystem libraries.

---

## Request Lifecycle

What happens from the moment a client sends `GET /api/school/students/42`:

```
1.  uvicorn receives the HTTP request → calls Rusjango.__call__(scope, receive, send)

2.  Rusjango.__call__ calls _build_asgi(), which lazily constructs the middleware
    stack (SecurityMiddleware wraps the core handler) and caches it.

3.  SecurityMiddleware.__call__ runs:
      - In production (DEBUG=False), validates the Host header against ALLOWED_HOSTS.
      - Injects security headers (X-Content-Type-Options, X-Frame-Options) into
        the response via a send_wrapper.

4.  The core ASGI handler runs:
      - Attaches settings to scope["rusjango"]["settings"].
      - Calls _match(method, path) — iterates routes, tests each compiled regex.

5.  Path parameters are extracted from the regex named groups:
        route.regex.match("/api/school/students/42") → {"id": "42"}

6.  Query string is parsed by parse_query_string:
        b"active=true&limit=10" → {"active": "true", "limit": "10"}

7.  For POST/PUT/PATCH, read_body reads all http.request chunks, then
    parse_json_body decodes the payload or raises HTTPException(422).

8.  call_handler inspects the handler's type hints:
      - Path params and query params are coerced (str → int, float, bool).
      - A remaining body-only param annotated with a Schema subclass is
        instantiated via Schema.from_dict(body).

9.  The handler coroutine is awaited. HTTPException bubbles up to send_error.
    Unhandled exceptions return a 500 envelope (with traceback if DEBUG=True).

10. The return value is serialised:
      dict  → send_json(200, result)
      list  → send_json(200, result)
      None  → send_json(204, {})
    json.dumps(default=str) handles datetime and other non-JSON types gracefully.
```

---

## Module Reference

| Module | File | Responsibility |
|---|---|---|
| `app` | `app.py` | `Rusjango` class: route decorators (`get`, `post`, `put`, `delete`), `include_router`, `load_installed_apps`, `__call__` (ASGI entry point), lazy middleware stack builder |
| `routing` | `routing.py` | `Route` dataclass, `compile_route` (path pattern → regex with named groups), `parse_query_string`, `coerce_param` (str → typed value), `call_handler` (param injection + Schema construction) |
| `asgi` | `asgi.py` | `read_body` (assembles chunked ASGI body), `parse_json_body` (JSON decode with 422 on error), `send_json` (serialise + send response), `send_error` (format and send HTTPException) |
| `middleware` | `middleware.py` | `ASGIApp` type alias, `import_string` (dotted path → class), `build_middleware_stack` (wraps core with each middleware class, last-listed = outermost, matching Django order) |
| `security` | `security.py` | `SecurityMiddleware`: reads `ALLOWED_HOSTS` and `DEBUG` from `scope["rusjango"]["settings"]`; blocks invalid Host headers in production; appends `X-Content-Type-Options` and `X-Frame-Options` to every response |
| `schema` | `schema.py` | `Schema` base class: `__init__` (kwargs filtered by type hints), `dict()` (typed attrs → dict), `from_dict(data)` (dict → Schema instance, unknown keys ignored) |
| `settings` | `settings.py` | `load_settings(path)`: imports a `settings.py` file via `importlib.util`, returns all uppercase names as a plain `dict[str, Any]` |
| `config` | `config.py` | `find_project_root`: walks up the directory tree until it finds a `pyproject.toml` containing `[tool.rusjango]`. `load_rusjango_config`: reads that file and returns the `[tool.rusjango]` table |
| `apps` | `apps.py` | `load_installed_apps`: iterates `INSTALLED_APPS`, imports each app's `api` module, mounts its `router` under `/api/<short_name>`, and imports each app's `models` module so model classes register themselves |
| `exceptions` | `exceptions.py` | `HTTPException(status_code, detail, headers)`: raised anywhere in a handler to abort with an HTTP error. `error_envelope`: produces `{"error": ..., "detail": ..., "status": ...}` |
| `server` | `server.py` | `run_dev`: reads `app` from `[tool.rusjango]`, `os.chdir`s to the project root, and calls `uvicorn.run` with an import string so file-change reload works |
| `router` | `router.py` | Module-level `router = Rusjango()` singleton and shortcut aliases (`get`, `post`, `put`, `delete`). Convenience import for single-file apps. Multi-app projects use `Router = Rusjango` from `__init__` instead |
| `orm/` | `orm/` | Async ORM: `Model` (metaclass-based field collection, CRUD class methods), `Field` types (`Integer`, `String`, `Text`, `Boolean`), `QuerySet` (chainable async filter/all/get/update/delete), `sql.py` (parameterised SQL generation), `connection.py` (aiosqlite / asyncpg pool) |

---

## Template System

Templates live in `templates/` and are plain text files with a `.tpl` extension. When the CLI renders a template, it strips the `.tpl` suffix from the output filename and performs three string replacements (implemented in `cli/src/project.rs::render_template`):

| Placeholder | Replaced with |
|---|---|
| `{{ project_name }}` | The name passed to `rusjango new <name>` |
| `{{ app_name }}` | The name passed to `rusjango add app <name>` |
| `{{ secret_key }}` | A 50-character random key generated from `[a-zA-Z0-9!@#$%^&*(-_=+)]` |

Example — `templates/project/settings.py.tpl` (excerpt):

```python
APP_NAME = "{{ project_name }}"
SECRET_KEY = "{{ secret_key }}"
```

Becomes `settings.py` with the actual project name and generated key. Templates are intentionally simple: no loops, no conditionals, no template engine dependency — just `str.replace`.

---

## CLI Architecture

The `rusjango` binary is a pure Rust executable (`cli/src/main.rs`). It never imports Python directly. Instead, for commands that need the Python runtime (`dev`, `migrate`), it spawns a subprocess:

```
rusjango dev
    └── try: uv run python -m rusjango._dev --host 127.0.0.1 --port 8000
        fallback: python -m rusjango._dev --host 127.0.0.1 --port 8000
```

`uv run` is tried first because it automatically activates the project's virtual environment. If `uv` is not on `PATH` (e.g., in a CI environment with a plain `python`), the fallback ensures the command still works.

For scaffolding commands (`new`, `add app`, `add orm`, `remove`), the CLI operates entirely in Rust — reading templates, writing files, and editing `settings.py` with regex — without spawning Python at all. This makes scaffolding instant and dependency-free.

```
rusjango new hello
    └── find templates_dir() → cli/../templates/project/
        render each .tpl file → write to hello/
        (no Python involved)

rusjango add app school
    └── find_project_root() → walk up from cwd, find [tool.rusjango]
        copy templates/app/ → apps/school/
        add "apps.school" to INSTALLED_APPS in settings.py
        inject app.load_installed_apps() into main.py if missing
        (no Python involved)
```

`templates_dir()` is resolved at compile time via `env!("CARGO_MANIFEST_DIR")`, which means the binary locates templates relative to its own source directory — important to understand when installing the binary outside the monorepo (a future release will embed templates in the binary with `include_str!`).
