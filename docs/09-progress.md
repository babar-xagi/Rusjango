# Project Progress

Phase-by-phase tracker for the Rusjango roadmap. Updated as features land.

---

## Phase 1: CLI + Minimal API Framework
**Status:** ✅ Complete

### What's included
- `rusjango new <name>` — scaffold a new project
- `rusjango dev` — start the development server (delegates to `uvicorn` via `uv run`)
- Basic routing: `GET`, `POST`, `PUT`, `DELETE`
- JSON responses (automatic serialization)
- Path parameters: `{id}`, `{slug}`, etc.
- Query parameters: resolved from `?key=value` pairs
- Settings loading from `settings.py`
- Middleware system with `build_middleware_stack`
- `SecurityMiddleware` (host validation + security headers)
- Structured error handling with optional debug tracebacks

### Files
- `cli/src/main.rs` — CLI entry point; defines `Commands` enum via `clap`
- `cli/src/new.rs` — `rusjango new` implementation; template rendering and project scaffolding
- `cli/src/dev.rs` — `rusjango dev` implementation; spawns `uv run uvicorn`
- `python/rusjango/src/rusjango/app.py` — `RusjangoApp` class; ASGI entry point
- `python/rusjango/src/rusjango/routing.py` — `Router` and `Route` classes; path-to-regex compilation; handler dispatch
- `python/rusjango/src/rusjango/asgi.py` — ASGI request/response helpers
- `python/rusjango/src/rusjango/middleware.py` — `build_middleware_stack`; middleware chain construction
- `python/rusjango/src/rusjango/security.py` — `SecurityMiddleware`
- `python/rusjango/src/rusjango/settings.py` — `load_settings`; uppercase-key extraction
- `python/rusjango/src/rusjango/exceptions.py` — `HttpException` and built-in HTTP error classes

---

## Phase 2: Add/Remove App System
**Status:** ✅ Complete

### What's included
- `rusjango add app <name>` — scaffolds app package, registers in `INSTALLED_APPS`
- `rusjango remove app <name>` — removes app directory, deregisters from `INSTALLED_APPS` (requires confirmation)
- `INSTALLED_APPS` is updated automatically in `settings.py` by Rust regex-based edit
- App router is mounted at `/api/<name>/` via the `apps.py` loader

### Files
- `cli/src/add.rs` — `rusjango add` subcommand; dispatches to app/orm/auth/etc. branches
- `cli/src/remove.rs` — `rusjango remove` subcommand; handles confirmation prompts
- `cli/src/settings.rs` — Rust helpers for reading and patching `settings.py` (regex-based)
- `python/rusjango/src/rusjango/apps.py` — `load_apps`; imports each app's `api.py` and mounts its router
- `templates/app/` — Jinja-style template files for new app scaffolding

---

## Phase 3: Async ORM Foundation
**Status:** ✅ Complete

### What's included
- `rusjango add orm` — installs ORM dependencies, adds `DATABASE` to `settings.py`
- `rusjango remove orm` — removes ORM config and dependencies
- `rusjango migrate` — creates all tables via `CREATE TABLE IF NOT EXISTS`
- SQLite support via `aiosqlite` (async, single persistent connection)
- PostgreSQL support via `asyncpg` (async, connection pool)
- `Model` base class with `ModelMeta` metaclass
- `Field` types: `IntField`, `CharField`, `BoolField`, `FloatField`, etc.
- CRUD operations: `create`, `get`, `filter`, `all`, `update`, `delete`
- Filter lookups: `exact` (default), `gte`, `lte`, `gt`, `lt`
- Schema helpers: `to_dict()` on model instances

### Files
- `cli/src/orm.rs` — `rusjango add orm` / `rusjango remove orm` / `rusjango migrate` implementations
- `python/rusjango/src/rusjango/orm/__init__.py` — public ORM exports
- `python/rusjango/src/rusjango/orm/model.py` — `Model`, `ModelMeta`, `_MODEL_REGISTRY`
- `python/rusjango/src/rusjango/orm/fields.py` — `Field` base class and all field types
- `python/rusjango/src/rusjango/orm/queryset.py` — lazy `QuerySet`; SQL building deferred to `.all()` / `.get()` / `.first()`
- `python/rusjango/src/rusjango/orm/sql.py` — SQL generation helpers (`create_table_sql`, `insert_sql`, `select_sql`, etc.)
- `python/rusjango/src/rusjango/orm/connection.py` — `configure_db`, `init_db`, `close_db`, `acquire` context manager
- `templates/orm/` — `settings.py` patch templates for `DATABASE` config block

---

## Phase 4: Schema and Validation System
**Status:** 🚧 Partial

### What's included
- Basic `Schema` class: ✅ (`from_dict`, `dict`, field introspection)
- Type coercion in routing for path/query params: ✅ (e.g., `id: int` from URL)
- Full body validation (type coercion, optional fields, nested schemas): 📋 Planned
- Detailed 422 validation error responses: 📋 Planned
- OpenAPI / JSON Schema generation: 📋 Planned

### Files
- `python/rusjango/src/rusjango/schema.py` — `Schema` base class; `from_dict` and `dict` methods
- `python/rusjango/src/rusjango/routing.py` — handler signature inspection; parameter source resolution (path / query / body / schema)

---

## Phase 5: Admin Panel MVP
**Status:** 📋 Planned

### What's included
- `rusjango add admin` CLI command
- Modern web UI (React + Tailwind CSS)
- Auto-generated CRUD views from registered `Model` classes
- Authentication-gated access
- Settings: `ADMIN = {"ENABLED": True, "PATH": "/admin", "THEME": "modern"}`

### Files
- TBD

---

## Phase 6: Auth and Security
**Status:** 📋 Planned

### What's included
- `rusjango add auth` CLI command
- `User` model with hashed passwords (argon2)
- JWT token generation and validation
- Session-based authentication
- Permission and role system
- `@require_auth` / `@require_role` route decorators
- Settings: `AUTH = {"ENABLED": True, "USER_MODEL": "...", "JWT": True, ...}`

### Files
- TBD

---

## Phase 7: Docs and Developer Experience
**Status:** 🚧 In Progress

### What's included
- CLI `--help` output for all commands: ✅
- `docs/` folder (this file and siblings): ✅ (in progress)
- Auto API documentation endpoint (`/docs`, `/openapi.json`): 📋 Planned
- Improved validation error messages (field-level detail): 📋 Planned
- Better startup error messages (e.g., misconfigured `DATABASE`): 📋 Planned

### Files
- `docs/` — all documentation files
- `python/rusjango/src/rusjango/routing.py` — will be extended for OpenAPI introspection

---

## Phase 8: Worker System
**Status:** 📋 Planned

### What's included
- `rusjango add worker` CLI command
- Async background task queue
- Redis broker via `aioredis`
- `@task` decorator for defining background jobs
- `task.delay(args)` to enqueue
- Settings: `WORKER = {"ENABLED": True, "BROKER": "redis://...", "ASYNC": True}`

### Files
- TBD

---

## Phase 9: AI/LLM Native Module
**Status:** 📋 Planned

### What's included
- `rusjango add ai` CLI command
- Unified provider interface (OpenAI, Anthropic, Ollama, etc.)
- Streaming response support (`text/event-stream`)
- Tool / function calling abstraction
- RAG (Retrieval-Augmented Generation) with vector store integration
- Settings: `AI = {"ENABLED": True, "DEFAULT_PROVIDER": "openai", "STREAMING": True, ...}`

### Files
- TBD

---

## Phase 10: Enterprise Features
**Status:** 📋 Planned

### What's included
- Advanced permission system (row-level security, attribute-based access control)
- Audit logging (who changed what, when)
- Multi-tenancy support (schema-per-tenant or row-per-tenant)
- Observability: OpenTelemetry traces, Prometheus metrics endpoint
- Plugin / extension system for third-party Rusjango packages
- Settings: `PAYMENTS`, advanced `AUTH` options

### Files
- TBD
