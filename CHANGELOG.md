# 📋 Changelog

All notable changes to Rusjango are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project follows [Semantic Versioning](https://semver.org/).

---

## [0.1.6] - 2026-10-06

### Added

- Independent admin registries, synchronous factories, and optional app discovery.
- Permission-gated catalog/list/detail services with explicit field projection, bounded pagination, strict filters, stable sorting, and literal search.
- Read-only defaults, opt-in typed writes, protected primary keys, and form metadata without default values.
- Shared admin add/remove scaffold in Python and Rust CLIs, with conflict checks and preservation of edits.
- Admin regressions on SQLite/PostgreSQL, fresh-wheel and Docker checks, and tutorial/reference documentation.

### Compatibility

- ADMIN accepts None or exactly a synchronous FACTORY configuration.
- AdminIdentity is supplied by trusted server code; authentication, login, and browser routes remain pending.
- Admin write inputs reject unknown fields. Existing API schema behavior is unchanged.

See [release notes](docs/releases/0.1.6.md) and [validation](docs/18-phase5-validation.md).

## [0.1.5] - 2026-10-06

### Added

- Opt-in coercion, Field range/length/pattern constraints, field validators, and cross-field validation.
- Docker/test add/remove commands in both CLIs with shared packaged templates and ownership-aware preservation.
- Production container configuration, isolated ASGI pytest fixtures, and Docker/distribution checks.

### Compatibility

- Strict validation stays the default; float fields reject non-finite values and overflow.
- Private annotations and ClassVar metadata are not schema fields.
- RUSJANGO_SETTINGS selects an override for explicit application settings and migrations.

See [release notes](docs/releases/0.1.5.md) for scope and validation.

## [0.1.4] - 2026-10-05

### Fixed

- Literal route matching, missing/invalid input errors, 405 `Allow` headers, and empty 204 responses.
- Production host validation, security headers on rejected requests, and ASGI lifespan cleanup.
- Independent model table names, concurrent SQLite insert results, null filters, and affected-row counts.
- PostgreSQL generated keys, update parameter numbering, and pooled connection release after failures.
- Python and Rust scaffolding preserve custom APIs and unrelated settings, honor configured settings paths, and propagate migration failures.
- Rust templates are embedded in the binary; native and Python versions are aligned at 0.1.4.
- Python 3.11+ package metadata and builds from the source distribution.

### Added

- Strict schema validation with defaults, optional types, nested schemas, lists, and dictionaries.
- Regression tests, both-CLI integration tests, real SQLite/PostgreSQL checks, and an installed-wheel smoke test.
- CI integration gates before release builds, clearer setup guides, and an evidence-based phase tracker.

### Compatibility

- Invalid schema types now return 422 instead of reaching handlers unchecked; JSON strings are not coerced to numbers.
- SQLite requires 3.35+ for `INSERT ... RETURNING`.
- Old databases affected by the `model` table-name bug need an explicit data migration. Corrected names do not move existing rows automatically.
- The Rust runtime remains a placeholder. Auth, admin, tracked migrations, and performance claims remain outside the implemented scope.

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

[0.1.4]: https://github.com/babar-xagi/Rusjango/releases/tag/v0.1.4

[0.1.6]: https://github.com/babar-xagi/Rusjango/releases/tag/v0.1.6
[0.1.5]: https://github.com/babar-xagi/Rusjango/releases/tag/v0.1.5
