# 🏗️ Architecture

**Rusjango 0.1.4 · Alpha**

This reference explains where each component lives and how a request moves through the framework. Start with the [tutorial](02-getting-started.md) if you are new to Rusjango.

## 📁 Repository map

| Directory | Responsibility |
|---|---|
| `python/rusjango/src/rusjango` | Application, Python CLI, schemas, middleware, and ORM |
| `python/rusjango/tests` | Runtime, CLI, regression, and PostgreSQL tests |
| `cli` | Standalone Rust CLI |
| `crates/rusjango-core` | PyO3 extension with version and placeholder function |
| `templates` | Templates embedded into the Rust binary |
| `examples/hello` | School API example |
| `scripts` | Release checks, distribution smoke tests, and disposable PostgreSQL runner |
| `docs` | Tutorials, references, internals, and release evidence |

## 🌐 Request flow

```text
Client → Uvicorn → Rusjango
                  ├─ Attach settings to the scope
                  ├─ Run HTTP middleware
                  ├─ Match a route
                  ├─ Bind and validate arguments
                  ├─ Await the handler
                  └─ Send the JSON response
```

Routes compile when registered and match in registration order. Middleware is built lazily and cached. Type hints and handler signatures are inspected during request dispatch.

## 🧩 Application mounting

Each installed app owns a fresh `Router()`. Loading `apps.school` mounts its endpoints under `/api/school/`.

Repeated `load_installed_apps()` calls do not duplicate already mounted apps. Models are imported when a database is configured.

## 🗃️ Database lifecycle

| Stage | Behavior |
|---|---|
| Application configuration | Select one process-wide database backend |
| ASGI startup | Configure the backend and acknowledge startup |
| First ORM operation | Open a connection or initialize the pool lazily |
| Explicit `migrate` | Create missing model tables |
| ASGI shutdown | Close the configured connection/pool and acknowledge shutdown |

SQLite operations share a serialized connection. Inserts read returned rows before commit. PostgreSQL operations acquire and release pool connections.

These mechanisms support individual CRUD operations. A public transaction API and independent per-app database configuration are pending.

## 🦀 Python and Rust responsibilities

| Component | Implemented role |
|---|---|
| Python runtime | Routing, parameter binding, schemas, middleware, JSON, and ORM |
| Python CLI | All published-package commands |
| Rust CLI | The same command surface with embedded templates |
| Rust core | Version export and placeholder `route_count` |

Request execution currently runs in Python. The extension is not connected to the Python route table.

## 🔎 Explore the implementation

- [Python internals](internals/python-layer.md)
- [ORM internals](internals/orm-internals.md)
- [Rust internals](internals/rust-core.md)

---

[📚 Documentation home](README.md) · [Contributing →](10-contributing.md)
