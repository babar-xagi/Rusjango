# ⚙️ Configure your application

**Rusjango 0.1.4 · Alpha**

The generated project stores runtime settings in `settings.py`. The application loads it with:

```python
from rusjango import Rusjango

app = Rusjango(settings="settings.py")
```

Rusjango executes the trusted Python file and collects its public uppercase names.

## 🧩 Apps and middleware

```python
INSTALLED_APPS = ["apps.school"]

MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",
]
```

Each installed package exposes `api.py` with a `router`. Keep `app.load_installed_apps()` in `main.py` to mount them.

The first middleware entry sees the request first and the response last.

## 🗃️ Database settings

Disable the ORM:

```python
DATABASE = None
```

Use SQLite:

```python
DATABASE = {
    "ENGINE": "sqlite",
    "NAME": "db.sqlite3",
}
```

The SQLite path is relative to the working directory. CLI operations run from the detected project root.

Use PostgreSQL with `rusjango[postgres]` installed:

```python
DATABASE = {
    "ENGINE": "postgresql",
    "URL": "postgresql://user:password@localhost:5432/demo",
    "MIN_SIZE": 1,
    "MAX_SIZE": 10,
}
```

One backend is configured per process. Close the current connection or pool before changing it.

> 💡 **ASYNC:** Generated configs may include `"ASYNC": True`. It is informational; ORM operations are always async.

## 🔒 Debug and allowed hosts

Generated projects use `DEBUG = True` for development.

For production-style host checking:

```python
DEBUG = False
ALLOWED_HOSTS = ["example.com", ".example.org"]
```

With `SecurityMiddleware` enabled:

- Exact names match that hostname.
- `.example.org` permits the base domain and its subdomains.
- `*` permits any valid hostname.
- An empty or missing allowlist rejects every host.
- Configure `::1` to allow bracketed IPv6 loopback requests.

`DEBUG = True` bypasses host validation and adds traceback detail to unexpected handler errors.

> 📌 **This is a host check:** It does not add authentication, HTTPS, CSRF protection, or rate limiting.

## 📋 Settings reference

| Setting | Current behavior |
|---|---|
| `APP_NAME` | Project metadata; available to application code |
| `DEBUG` | Enables error tracebacks and skips host validation |
| `ALLOWED_HOSTS` | Host allowlist used by SecurityMiddleware |
| `INSTALLED_APPS` | Application packages to mount |
| `MIDDLEWARE` | Ordered list of ASGI middleware classes |
| `DATABASE` | None, SQLite, or PostgreSQL configuration |
| `SECRET_KEY` | Reserved; the framework currently does not use it for signing/auth |
| `AUTH`, `ADMIN`, `AI`, `WORKER`, `PAYMENTS` | Reserved placeholders with no implemented feature behavior |

## 📄 Project entry point

The CLI reads these keys from `pyproject.toml`:

```toml
[tool.rusjango]
settings = "settings.py"
app = "main:app"
```

`app` selects the object served by the development command. `settings` selects the file edited by app/ORM commands.

If you rename the settings file, also update the `Rusjango(settings=...)` argument in your application code. That constructor does not infer its path from the CLI configuration.

## ✍️ CLI editing rules

App/ORM commands edit literal `INSTALLED_APPS` lists and `DATABASE` dictionaries/None values. Computed settings require manual editing.

Unrelated settings are preserved. Formatting and comments inside the edited value may be normalized.

---

[← Async ORM](05-orm-guide.md) · [📚 Documentation home](README.md) · [Next: Middleware →](07-middleware.md)
