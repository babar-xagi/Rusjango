# Changelog

All notable changes to Rusjango are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project follows [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2025-05-27

First public release. Phases 1–3 complete.

### Added

**CLI (`rusjango` binary — Rust / clap)**
- `rusjango new <name>` — scaffold a minimal 3-file project (`main.py`, `settings.py`, `pyproject.toml`)
- `rusjango dev` — start uvicorn dev server with auto-reload; options: `--host`, `--port`, `--no-reload`
- `rusjango add app <name>` — scaffold `apps/<name>/` and register in `INSTALLED_APPS`
- `rusjango remove app <name>` — remove app with confirmation prompt (`--yes` to skip)
- `rusjango add orm` — enable async ORM (SQLite default); adds `models.py`, `schemas.py`, `migrations/`
- `rusjango remove orm` — set `DATABASE = None`; keeps model files
- `rusjango migrate` — create database tables from all registered models

**Python framework**
- `Rusjango` ASGI 3.0 application class with `@app.get`, `@app.post`, `@app.put`, `@app.delete`
- `Router` — per-app router class (alias for `Rusjango`); each app creates its own isolated instance
- Path parameters with automatic type coercion (`int`, `float`, `bool`, `str`)
- Query string parameters
- JSON request body parsing
- `Schema` — lightweight typed request/response class
- `HTTPException` — raise to return structured error responses
- Middleware chain (`MIDDLEWARE` setting) — ASGI-compatible class-based middleware
- `SecurityMiddleware` — `Host` header validation + `X-Frame-Options` / `X-Content-Type-Options` headers
- `INSTALLED_APPS` auto-loading — mounts each app's `router` under `/api/<app_name>/`
- `load_installed_apps()` — mounts all registered app routers
- Settings loader — loads any Python file as a plain dict of uppercase names
- Debug tracebacks in error responses when `DEBUG = True`

**Async ORM**
- `Model` base class with `ModelMeta` metaclass
- Field types: `Integer`, `String`, `Text`, `Boolean`
- `Model.create(**kwargs)` — insert and return instance
- `Model.get(**filters)` — fetch one or raise `DoesNotExist` / `MultipleObjectsReturned`
- `Model.all()` — fetch all rows
- `Model.filter(**lookups)` — return `QuerySet`
- `QuerySet.all()`, `.first()`, `.get()`, `.update()`, `.delete()`
- Filter lookups: `exact` (default), `gte`, `lte`, `gt`, `lt`
- SQLite backend via `aiosqlite`
- PostgreSQL backend via `asyncpg`
- `rusjango migrate` — `CREATE TABLE IF NOT EXISTS` for all registered models

**Documentation**
- 14 `.md` files in `docs/` covering overview, architecture, getting started, CLI reference, API design, ORM guide, settings, middleware, schema, progress, contributing, and internals

**Tests**
- 13 tests across 5 test files: import, ASGI routing, app loading, config discovery, ORM CRUD

### Notes
- The `rusjango._core` Rust extension is included in platform wheels; the pure Python fallback is used automatically if the extension is unavailable.
- PostgreSQL requires the optional `asyncpg` dependency: `uv add rusjango[postgres]`

[0.1.0]: https://github.com/babar-xagi/Rusjango/releases/tag/v0.1.0
