# 🧪 Test your application

**Rusjango 0.1.6 · Alpha**

The test scaffold provides a small asynchronous ASGI client and a starter endpoint test. It uses pytest and pytest-asyncio.

## 📁 Add tests

Inside your project:

```bash
uv run rusjango add tests
```

Generated files:

```text
tests/
├── conftest.py
└── test_health.py
```

The project also receives `.rusjango-features.json` to track original scaffold content. Existing conftest/test files are never overwritten.

## ▶️ Run them

```bash
uv run --with pytest --with pytest-asyncio pytest tests
```

The `--with` flags provide test dependencies without changing the project's dependency list.

If you prefer to record them:

```bash
uv add --dev pytest pytest-asyncio
uv run pytest tests
```

The generated home test expects the starter route to return `{"message": "Hello Rusjango"}`. Adapt it if your application's home route differs.

## ✍️ Write an API test

With the school ORM API enabled, add `tests/test_students.py`:

```python
import pytest


@pytest.mark.asyncio
async def test_create_student(client):
    response = await client.request(
        "POST", "/api/school/students", json={"name": "Sara"}
    )

    assert response.status == 200
    assert response.json()["name"] == "Sara"
    assert response.json()["age"] is None


@pytest.mark.asyncio
async def test_invalid_name(client):
    response = await client.request(
        "POST", "/api/school/students", json={"name": 123}
    )

    assert response.status == 422
```

Query strings go in the path, for example `client.request("GET", "/search?limit=5")`.

| Response member | Meaning |
|---|---|
| `status` | HTTP status integer |
| `body` | Raw response bytes |
| `headers` | Byte-key/byte-value mapping |
| `.json()` | Parsed JSON body; do not call it on empty 204 output |

## 🔒 Database isolation

For applications with ORM configured, each test gets a fresh in-memory SQLite database and missing tables are created explicitly. Application database files and PostgreSQL connections are not used by this fixture.

The fixture temporarily allows `testserver` as the host, clears `RUSJANGO_SETTINGS` for import, and restores application settings afterward. It closes connections during cleanup.

> 💡 **Backend-specific behavior:** SQLite tests do not establish PostgreSQL behavior. Add a dedicated disposable PostgreSQL fixture when you need database-specific SQL or constraints. Rusjango still supports one configured backend per process.

## 🔎 What the client does

The client calls the ASGI application directly. It does not start a network server or exercise the ASGI lifespan protocol.

The fixture reads the configured `[tool.rusjango].app` object, so it does not hardcode `main:app`.

Use a real Uvicorn/container check for network and lifecycle behavior. The framework's [validation record](16-phase4-validation.md) includes those checks.

## 🧹 Remove scaffolding

```bash
uv run rusjango remove tests
```

Unchanged generated files are removed after confirmation. Modified files and additional user-written tests stay intact. Cached directories may remain.

Keep the ownership manifest with the generated files. `--yes` skips the confirmation prompt, not the preservation checks.

---

[← Docker](14-docker.md) · [📚 Documentation home](README.md) · [CLI reference →](03-cli-reference.md)
