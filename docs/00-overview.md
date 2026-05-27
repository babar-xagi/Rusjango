# Rusjango — Project Overview

> **Start like Flask, scale like Django, perform like Rust, and build AI apps natively.**

---

## What is Rusjango?

Rusjango is a Rust-accelerated, fully async Python web framework designed to feel lightweight at the start and grow with the project. It combines a minimal Flask-like developer API (a single `Rusjango` class, plain decorators, no boilerplate) with Django's project-structure conventions (apps, settings, installed apps, middleware list) and Rust's performance ceiling (a compiled extension via PyO3 handles the hot path). A developer can scaffold a working API in three commands, add an app or ORM with one command, and remove features just as easily. The entire stack — CLI, core extension, Python layer, and ORM — lives in one monorepo so contributors work on everything in one place.

---

## Problems it Solves

| Problem | Django behavior | Rusjango solution |
|---|---|---|
| **Old sync foundation** | Built on WSGI; async requires `async_to_sync` adapters | Pure ASGI 3.0 from the first line; every handler is `async def` |
| **Heavy project structure** | `startproject` generates urls.py, wsgi.py, asgi.py, manage.py, migrations/, admin.py before writing a single route | `rusjango new` generates four files: `main.py`, `settings.py`, `pyproject.toml`, and nothing else |
| **ORM not async-native** | `django.db` is synchronous; `sync_to_async` wrappers add thread overhead | ORM is async first: `await Student.all()`, `await Student.create(...)` — no wrapper needed |
| **Admin UI feels old** | django.contrib.admin is tightly coupled to the sync ORM and template engine | Admin is a first-class opt-in (`ADMIN = ...` in settings), not bundled by default |
| **DRF needed for APIs** | Building a JSON API requires installing Django REST Framework separately | JSON responses are the native format; no third-party package needed |
| **Not AI-native** | No concept of AI, vector stores, or LLM tooling in core | `AI = ...` settings slot reserved; AI features are first-class add-ons, not afterthoughts |
| **Performance limits** | Pure Python request handling; every request goes through Python-only middleware | Rust extension (`rusjango._core`) provides the performance floor; routing acceleration is roadmapped |
| **Boilerplate grows fast** | Every new model needs forms, serializers, views, urls, and admin registration | `rusjango add orm` generates model, schema, and ORM-wired API routes in one step |

---

## Target Users

| User type | Need | Rusjango support |
|---|---|---|
| **Beginner** | Something simpler than Django, faster to run than setting up a full project | Four-file scaffold, one command to start the server |
| **FastAPI user** | Familiar async decorator API but wants a more structured project model | Same `@app.get("/")` pattern plus settings, apps, and a real ORM |
| **Django user** | Keep `INSTALLED_APPS`, `MIDDLEWARE`, `settings.py` habits but go async | All three conventions are preserved; migration path is additive |
| **Startup founder** | Ship fast, scale later, don't rewrite | Progressive growth model: add features without restructuring |
| **Enterprise team** | Monorepo, testable units, CI-friendly | Rust workspace + uv workspace; full pytest suite; typed Python throughout |
| **AI developer** | Native AI tooling without duct-tape integrations | `AI` settings slot; async handlers work seamlessly with async AI client libraries |
| **Data scientist** | Quick API around a model or dataset without learning a new stack | Minimal API; `Schema` for typed I/O; SQLite ORM for local data |
| **Freelancer** | Deliver fast, hand off cleanly | Clear app separation, readable conventions, one-command setup for new contributors |

---

## Core Philosophy

**Minimal by default. Powerful when needed.**

A new Rusjango project has no ORM, no admin, no auth, no worker queue. Every one of those is an explicit `rusjango add` command. The settings file documents every future slot (`DATABASE`, `AUTH`, `ADMIN`, `AI`, `WORKER`, `PAYMENTS`) as `None`, so the surface area of the project is always visible even when most of it is turned off.

---

## The Progressive Growth Model

Rusjango projects grow by explicit command rather than silent convention:

```
rusjango new my-api       # scaffold a four-file project
cd my-api && rusjango dev # running in seconds

rusjango add app orders   # add a new app package under apps/
rusjango add orm          # enable async ORM, create migrations/
rusjango migrate          # create tables

rusjango remove app orders  # remove an app (with confirmation)
rusjango remove orm         # disable ORM (keeps migration files)
```

The project structure at any point reflects exactly what has been opted into. Nothing is hidden.

---

## Technology Stack

| Layer | Technology | Why |
|---|---|---|
| **Rust CLI** | `clap` 4 | Compiles to a fast native binary (`rusjango`); generates consistent, self-documenting `--help` output with zero runtime overhead |
| **Rust core** | `PyO3`, `tokio`, `hyper` (roadmap) | PyO3 bridges Rust and Python without a subprocess; tokio provides the async runtime for future I/O acceleration; hyper is the HTTP primitive for connection pooling work |
| **Python layer** | Pure Python 3.10+ | The developer-facing API stays in Python so business logic, type hints, and IDE tooling work without any Rust knowledge |
| **Database** | `aiosqlite` (SQLite), `asyncpg` (PostgreSQL) | Both are native async drivers — no thread pool, no sync wrapper; aiosqlite is bundled by default, asyncpg is an optional extra (`rusjango[postgres]`) |
| **Packaging** | `uv` + `maturin` | `uv` manages the Python workspace and virtual environments at Rust speed; `maturin` builds and installs the PyO3 extension (`_core.pyd` / `_core.so`) in one command |
| **Dev server** | `uvicorn` | ASGI 3.0 compliant, production-ready, supports `--reload`; Rusjango passes an import string (`main:app`) so uvicorn can restart the process on file changes |
