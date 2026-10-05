# 🦀 Welcome to Rusjango

**Rusjango 0.1.4 · Alpha**

Rusjango is an async Python API framework with Django-style application packages. It begins with a small project and lets you add app and database scaffolding through the CLI.

## 🌱 Start small

A new project contains three files:

```text
demo/
├── main.py          # Routes and application object
├── settings.py      # Runtime configuration
└── pyproject.toml   # Dependencies and CLI project settings
```

Write an async function, register a route, and return JSON-compatible data:

```python
from rusjango import Rusjango

app = Rusjango()


@app.get("/")
async def home():
    return {"message": "Hello Rusjango"}
```

Save this standalone example as `main.py` and run `python -m uvicorn main:app --reload` in an environment with Rusjango installed.

## 🧩 Grow your project

| When you need… | Use… |
|---|---|
| Another group of endpoints | `rusjango add app school` |
| Validated JSON input | A `Schema` subclass |
| A database | `rusjango add orm`, then `rusjango migrate` |
| Project configuration | `settings.py` |
| Request/response hooks | ASGI middleware |

Applications own independent `Router()` instances. An app named `school` is mounted under `/api/school/`.

Adding ORM creates starter model/schema files. An untouched starter API can be upgraded; custom API files stay intact.

## ⚙️ How it runs

Uvicorn serves the ASGI application. Routing, middleware, validation, and JSON serialization run in Python. SQLite uses aiosqlite; PostgreSQL uses the optional asyncpg driver.

The Python package includes the full CLI. A separate Rust CLI implements the same commands with embedded templates.

> 📌 **Rust status:** The native extension currently exports version information and a placeholder function. Rust request acceleration is planned; no benchmark advantage is claimed.

## 🧭 Choose it with the current scope in mind

Use Rusjango for experimentation and contribution. The ORM supports basic CRUD and table creation, with one database per process. It does not yet provide relationships, transaction APIs, or tracked schema migrations.

Auth, admin, OpenAPI, Docker/test scaffolding, workers, and AI integrations remain planned features.

[PROGRESS.md](../PROGRESS.md) tracks the phases. The [validation record](11-validation.md) documents what has been tested.

---

[📚 Documentation home](README.md) · [Next: First steps →](02-getting-started.md)
