# Rusjango — Build Progress

> **Tagline:** Start like Flask, scale like Django, perform like Rust, build AI apps natively.

This file is the single source of truth for what has been built, what is in progress, and what is planned.
See `docs/09-progress.md` for deeper per-phase notes with file references.

---

## Current Status: Phase 3 Complete ✅

```
Phase 1: CLI + Minimal API Framework        ✅  Complete
Phase 2: Add/Remove App System              ✅  Complete
Phase 3: Async ORM Foundation               ✅  Complete
Phase 4: Schema and Validation System       🚧  Partial (basic Schema done)
Phase 5: Admin Panel MVP                    📋  Planned
Phase 6: Auth and Security                  📋  Planned
Phase 7: Docs and Developer Experience      🚧  In Progress (this docs/ folder)
Phase 8: Worker System                      📋  Planned
Phase 9: AI/LLM Native Module               📋  Planned
Phase 10: Enterprise Features               📋  Planned
```

---

## What Works Right Now

### CLI Commands

| Command | Status |
|---|---|
| `rusjango new <name>` | ✅ Creates minimal 3-file project |
| `rusjango dev` | ✅ uvicorn dev server with auto-reload |
| `rusjango add app <name>` | ✅ Scaffolds app, registers in INSTALLED_APPS |
| `rusjango remove app <name>` | ✅ Removes app with confirmation prompt |
| `rusjango add orm` | ✅ Enables SQLite ORM, adds models/schemas |
| `rusjango remove orm` | ✅ Disables ORM, keeps files |
| `rusjango migrate` | ✅ Creates tables from models |
| `rusjango add admin` | 📋 Planned — Phase 5 |
| `rusjango add auth` | 📋 Planned — Phase 6 |
| `rusjango add ai` | 📋 Planned — Phase 9 |
| `rusjango add worker` | 📋 Planned — Phase 8 |
| `rusjango add docker` | 📋 Planned — Phase 2.x |
| `rusjango add tests` | 📋 Planned — Phase 2.x |
| `rusjango add payments` | 📋 Planned — Phase 10 |

### Python Framework

| Feature | Status |
|---|---|
| ASGI 3.0 application | ✅ |
| GET / POST / PUT / DELETE routes | ✅ |
| Path parameters (auto type coercion) | ✅ |
| Query parameters | ✅ |
| JSON request body | ✅ |
| Schema class (request/response) | ✅ |
| Middleware chain | ✅ |
| SecurityMiddleware (host + headers) | ✅ |
| INSTALLED_APPS mounting | ✅ |
| Per-app Router isolation | ✅ (fixed in this session) |
| Settings loader | ✅ |
| HTTPException | ✅ |
| Debug tracebacks | ✅ |

### Async ORM

| Feature | Status |
|---|---|
| SQLite (aiosqlite) | ✅ |
| PostgreSQL (asyncpg) | ✅ Connection support |
| Integer / String / Text / Boolean fields | ✅ |
| `Model.create()` | ✅ |
| `Model.get()` | ✅ |
| `Model.filter(**lookups).all()` | ✅ |
| `QuerySet.update()` | ✅ |
| `QuerySet.delete()` | ✅ |
| Filter lookups: exact, gte, lte, gt, lt | ✅ |
| `rusjango migrate` (CREATE TABLE) | ✅ |
| Relationships (FK, M2M) | 📋 Planned — Phase 3.x |
| Full migration tracking | 📋 Planned — Phase 3.x |

### Documentation

| Doc file | Status |
|---|---|
| `docs/00-overview.md` | ✅ |
| `docs/01-architecture.md` | ✅ |
| `docs/02-getting-started.md` | ✅ |
| `docs/03-cli-reference.md` | ✅ |
| `docs/04-api-design.md` | ✅ |
| `docs/05-orm-guide.md` | ✅ |
| `docs/06-settings-reference.md` | ✅ |
| `docs/07-middleware.md` | ✅ |
| `docs/08-schema-validation.md` | ✅ |
| `docs/09-progress.md` | ✅ |
| `docs/10-contributing.md` | ✅ |
| `docs/internals/rust-core.md` | ✅ |
| `docs/internals/python-layer.md` | ✅ |
| `docs/internals/orm-internals.md` | ✅ |

---

## Test Coverage

```
tests/test_import.py      — package imports cleanly
tests/test_asgi.py        — routing, path params, POST body, HTTPException
tests/test_apps.py        — INSTALLED_APPS loading, router isolation (multi-app)
tests/test_config.py      — pyproject.toml discovery
tests/test_orm.py         — CRUD, filters, update, delete (SQLite)
```

Run with:
```bash
cd python/rusjango
uv run pytest tests/ -v
```

**Result: 13 / 13 passing**

---

## Next Steps

### Immediate (Phase 4 completion)
- [ ] Full Schema validation (type coercion, required fields, defaults)
- [ ] `rusjango add docker` — generate Dockerfile + docker-compose.yml
- [ ] `rusjango add tests` — generate test scaffolding

### Phase 5 (Admin Panel)
- [ ] `rusjango add admin` CLI command
- [ ] React + Tailwind admin UI
- [ ] Auto CRUD from model registry
- [ ] `apps/*/admin.py` scaffolding

### Phase 6 (Auth)
- [ ] `rusjango add auth` CLI command
- [ ] User model + argon2 password hashing
- [ ] JWT token generation + validation
- [ ] Session support
- [ ] `apps/accounts/` scaffolding

---

## Repository Structure

```
rusjango/
├── Cargo.toml              Rust workspace (core + CLI)
├── pyproject.toml          uv workspace root
├── PROGRESS.md             This file
├── README.md               Quick-start readme
├── crates/rusjango-core/   PyO3 Rust extension (future routing acceleration)
├── cli/                    rusjango binary (clap)
├── python/rusjango/        Python package (maturin)
│   ├── src/rusjango/       Framework source
│   └── tests/              All tests
├── templates/              .tpl code generation templates
├── examples/hello/         Working example project
└── docs/                   All documentation (14 files)
```
