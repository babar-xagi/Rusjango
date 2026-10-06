# 🦀 Rusjango

**Async Python APIs. Django-style apps. Add features as you go.**

[![PyPI](https://img.shields.io/pypi/v/rusjango?color=2563eb)](https://pypi.org/project/rusjango/)
[![Python](https://img.shields.io/pypi/pyversions/rusjango)](https://pypi.org/project/rusjango/)
[![CI](https://github.com/babar-xagi/Rusjango/actions/workflows/ci.yml/badge.svg)](https://github.com/babar-xagi/Rusjango/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/babar-xagi/Rusjango/blob/main/LICENSE)

[📚 Documentation](https://github.com/babar-xagi/Rusjango/blob/main/docs/README.md) · [🚀 First steps](https://github.com/babar-xagi/Rusjango/blob/main/docs/02-getting-started.md) · [📦 Releases](https://github.com/babar-xagi/Rusjango/releases) · [💬 Issues](https://github.com/babar-xagi/Rusjango/issues)

Rusjango is an async Python web framework that starts with a three-file project. Write a route, add an application, and enable a database when you need one.

> 🧪 **Version 0.1.5 · Alpha.** Routing, validation extensions, app/ORM/Docker/test scaffolding, and basic async ORM are implemented. The Rust CLI works today; the native runtime extension is a placeholder. Request handling currently runs in Python.

## ✨ What you can build with it

| Feature | What you get |
|---|---|
| **Async APIs** | GET, POST, PUT, and DELETE handlers with JSON responses |
| **Typed inputs** | Strict schemas, opt-in coercion, Field constraints, and synchronous validators |
| **Organized apps** | Independent routers mounted under `/api/<app>/` |
| **Async ORM** | SQLite and PostgreSQL create, read, update, and delete |
| **Progressive scaffolding** | CLI commands that preserve custom APIs and unrelated settings |
| **Middleware** | ASGI middleware, Host validation, and basic security headers |
| **Two CLIs** | Python CLI in the package and a standalone Rust CLI |
| **Docker and tests** | Nonroot container scaffold and isolated ASGI pytest fixture |

## 🚀 Quick start

You need **Python 3.11+** and [uv](https://docs.astral.sh/uv/getting-started/installation/).

### 1. Create your project

```bash
uvx --from rusjango==0.1.5 rusjango new demo
cd demo
uv sync
```

The scaffold starts with:

```text
demo/
├── main.py
├── settings.py
└── pyproject.toml
```

### 2. Run it

```bash
uv run rusjango dev
```

Open **http://127.0.0.1:8000/**:

```json
{"message": "Hello Rusjango"}
```

> 💡 **Prefer pip?** See the [pip installation steps](https://github.com/babar-xagi/Rusjango/blob/main/docs/02-getting-started.md#install-with-pip). Rust is needed for source builds, not for installing a compatible published wheel.

### 3. Write a typed API

Replace `main.py` with:

```python
from rusjango import Rusjango, Schema

app = Rusjango(settings="settings.py")


class Greeting(Schema):
    name: str
    age: int | None = None


@app.get("/")
async def home():
    return {"message": "Hello Rusjango"}


@app.get("/hello/{name}")
async def hello(name: str, excited: bool = False):
    message = f"Hello {name}"
    return {"message": message + ("!" if excited else "")}


@app.post("/greetings")
async def create_greeting(data: Greeting):
    return data.dict()


app.load_installed_apps()
```

Try a path and query parameter:

```bash
curl "http://127.0.0.1:8000/hello/Ali?excited=true"
```

```json
{"message": "Hello Ali!"}
```

Send a JSON body:

```bash
curl -X POST http://127.0.0.1:8000/greetings \
  -H "Content-Type: application/json" -d '{"name":"Ali"}'
```

```json
{"name": "Ali", "age": null}
```

JSON schema types are strict: `"20"` is not an integer. Invalid input returns **422**. Defaults make fields omittable; unknown JSON keys are ignored.

## 🧩 Add an application

Stop the server with **Ctrl+C**, then run:

```bash
uv run rusjango add app school
uv run rusjango dev
```

Visit **http://127.0.0.1:8000/api/school/students**.

Each app has its own `Router()`. The CLI creates its package and registers it in `INSTALLED_APPS`.

## 🗃️ Add a database

Stop the server again, then:

```bash
uv run rusjango add orm
uv run rusjango migrate
uv run rusjango dev
```

The untouched school starter now reads and writes SQLite:

```bash
curl -X POST http://127.0.0.1:8000/api/school/students \
  -H "Content-Type: application/json" -d '{"name":"Sara","age":22}'
curl http://127.0.0.1:8000/api/school/students
```

`add orm` adds model/schema files and upgrades an API only if it still matches the original starter. Custom API files are preserved.

> 💡 **About migrations:** `migrate` creates missing tables. It does not alter existing columns or move data. Run it explicitly before database-backed requests; startup does not create tables.

PostgreSQL is supported through the optional `rusjango[postgres]` dependency. Follow the [ORM guide](https://github.com/babar-xagi/Rusjango/blob/main/docs/05-orm-guide.md) to configure it.

## 🐳 Containers and 🧪 application tests

```bash
uv run rusjango add tests
uv run --with pytest --with pytest-asyncio pytest tests

uv run rusjango add docker
export ALLOWED_HOSTS=localhost,127.0.0.1
docker compose build
docker compose run --rm web /app/.venv/bin/python -m rusjango migrate
docker compose up -d
```

Run the migration command only when ORM is enabled. Container settings disable debug and use a named volume for SQLite. Generated tests use an in-memory SQLite database per test.

`remove docker` and `remove tests` delete only unchanged tracked files and preserve edits. Follow the [Docker guide](https://github.com/babar-xagi/Rusjango/blob/main/docs/14-docker.md) and [testing guide](https://github.com/babar-xagi/Rusjango/blob/main/docs/15-testing.md) for configuration.

## 🛠️ CLI at a glance

Run these inside your project with `uv run rusjango`:

| Command | Purpose |
|---|---|
| `new <name>` | Create a minimal project |
| `dev` | Start the development server with reload |
| `add app <name>` | Scaffold and register an app |
| `remove app <name>` | Confirm, unregister, and delete an app |
| `add orm` | Add SQLite configuration and ORM starter files |
| `remove orm` | Disable ORM while keeping application files |
| `migrate` | Create missing model tables |
| `add docker` / `remove docker` | Add/remove unchanged tracked container files |
| `add tests` / `remove tests` | Add/remove unchanged tracked pytest files |

See the [CLI reference](https://github.com/babar-xagi/Rusjango/blob/main/docs/03-cli-reference.md) for flags, naming rules, and preservation behavior.

## 📚 Learn step by step

| Start here | Then learn |
|---|---|
| [First steps](https://github.com/babar-xagi/Rusjango/blob/main/docs/02-getting-started.md) | Install, create, run, and check your first API |
| [Routes and requests](https://github.com/babar-xagi/Rusjango/blob/main/docs/04-api-design.md) | Paths, query parameters, JSON bodies, and errors |
| [Schemas](https://github.com/babar-xagi/Rusjango/blob/main/docs/08-schema-validation.md) | Required fields, defaults, nesting, and validation |
| [Applications](https://github.com/babar-xagi/Rusjango/blob/main/docs/13-applications.md) | Split your API into independent app packages |
| [Async ORM](https://github.com/babar-xagi/Rusjango/blob/main/docs/05-orm-guide.md) | Models, CRUD, SQLite, and PostgreSQL |
| [Settings](https://github.com/babar-xagi/Rusjango/blob/main/docs/06-settings-reference.md) | Configure apps, middleware, and database access |
| [Middleware](https://github.com/babar-xagi/Rusjango/blob/main/docs/07-middleware.md) | Wrap requests and use the built-in host checks |
| [Docker](https://github.com/babar-xagi/Rusjango/blob/main/docs/14-docker.md) | Configure containers and persistent data |
| [Application tests](https://github.com/babar-xagi/Rusjango/blob/main/docs/15-testing.md) | Run an ASGI client with isolated database fixtures |

The [documentation home](https://github.com/babar-xagi/Rusjango/blob/main/docs/README.md) also links to architecture, internals, validation, and release guides.

## 🔬 Develop from source

Clone the repository and install the development environment:

```bash
git clone https://github.com/babar-xagi/Rusjango.git
cd Rusjango
uv sync --all-packages --all-extras
cargo build -p rusjango-cli

cd examples/hello
uv run rusjango migrate
uv run rusjango dev
```

The repository pins Python 3.12. Set `UV_PYTHON=3.14` to use Python 3.14. Windows and WSL virtual environments cannot be shared.

**Phase 4 checks:** 122 tests passed on Python 3.11 and 3.14 with both CLIs and live PostgreSQL. Rust checks, distribution builds, and fresh installed-wheel/generated-test checks passed. Container and hosted gates are recorded separately in the [Phase 4 validation record](https://github.com/babar-xagi/Rusjango/blob/main/docs/16-phase4-validation.md).

[🤝 Contributing](https://github.com/babar-xagi/Rusjango/blob/main/docs/10-contributing.md) · [✅ Validation record](https://github.com/babar-xagi/Rusjango/blob/main/docs/11-validation.md)

## 🧭 Current scope

Rusjango is suitable for experimentation and contribution. It has one database configuration per process and no transaction API, relationships, or tracked schema migrations. SQLite needs **3.35+**. Request bodies are buffered in memory.

Auth, admin, OpenAPI/Swagger generation, workers, uploads, streaming, and supported WebSockets remain pending. There are no benchmarks proving a performance advantage.

> 📌 **Upgrading an old database?** Earlier versions could use a default table named `model`. Back up the data and migrate it explicitly to the corrected table names. This release does not rename that table automatically.

Follow [PROGRESS.md](https://github.com/babar-xagi/Rusjango/blob/main/PROGRESS.md) for implemented and planned phases, and the [0.1.5 release notes](https://github.com/babar-xagi/Rusjango/blob/main/docs/releases/0.1.5.md) for compatibility changes.

## 📄 License

Rusjango is released under the [MIT license](https://github.com/babar-xagi/Rusjango/blob/main/LICENSE).
