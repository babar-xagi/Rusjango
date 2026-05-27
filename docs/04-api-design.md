# API Design Guide

This document covers every part of Rusjango's Python API: the application object, route decorators, parameter handling, request bodies, response formats, routers, and middleware.

---

## Application object

```python
from rusjango import Rusjango

app = Rusjango(settings="settings.py")
```

`Rusjango` is both the application factory and the ASGI 3.0 callable. A single instance serves as the top-level app passed to uvicorn.

### Constructor parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `settings` | `str \| None` | `None` | Path to a `settings.py` file, relative to the current working directory. Optional — omit it for single-file scripts that do not need settings. |

### What happens at startup

1. If `settings` is provided, the settings file is imported and all uppercase module-level variables are collected into `app.settings` (a plain `dict`).
2. If `app.settings["DATABASE"]` is set (not `None`), `configure_db(DATABASE)` is called immediately so that the ORM connection is ready before any request arrives.
3. Middleware is **not** assembled at construction time — it is built lazily on the first request and cached.

---

## Route decorators

```python
@app.get("/")
@app.post("/items")
@app.put("/items/{id}")
@app.delete("/items/{id}")
```

All four decorators accept an HTTP method and a URL pattern. The decorated function must be `async`. The decorator returns the original function unchanged, so it can still be called directly in tests.

```python
@app.get("/")
async def home():
    return {"message": "Hello Rusjango"}

@app.post("/items")
async def create_item():
    ...

@app.put("/items/{id}")
async def update_item(id: int):
    ...

@app.delete("/items/{id}")
async def delete_item(id: int):
    ...
```

---

## Path parameters

Curly-brace placeholders in the route pattern become path parameters:

```python
@app.get("/students/{id}")
async def get_student(id: int):
    return {"id": id}
```

The parameter name in the function signature must match the placeholder name exactly. Type annotations are used to coerce the raw string captured from the URL:

| Annotation | Coercion |
|---|---|
| `int` | `int(value)` |
| `float` | `float(value)` |
| `bool` | `True` if value is `"1"`, `"true"`, `"yes"`, or `"on"` (case-insensitive) |
| `str` (default) | No coercion — raw string |

If coercion fails (e.g. `"abc"` → `int`), Python raises a `ValueError` which is caught and returned as a `500` response.

Multiple path parameters are supported:

```python
@app.get("/courses/{course_id}/students/{student_id}")
async def get_student_in_course(course_id: int, student_id: int):
    return {"course": course_id, "student": student_id}
```

---

## Query parameters

Any function parameter that is **not** present in the path pattern is treated as a query parameter:

```python
@app.get("/students")
async def list_students(limit: int = 10, search: str = ""):
    return {"limit": limit, "search": search}
```

A request to `/students?limit=5&search=ali` calls `list_students(limit=5, search="ali")`.

The same type coercion rules apply as for path parameters. Parameters with default values are optional; parameters without defaults are required (if absent, the handler is called without that argument, which raises a `TypeError` → `500`).

---

## Request body

### Schema (typed body)

Define a `Schema` subclass and use it as the type annotation for a body parameter:

```python
from rusjango import Schema

class StudentCreate(Schema):
    name: str
    age: int

@app.post("/students")
async def create_student(data: StudentCreate):
    return data.dict()
```

The framework reads the raw request body, parses it as JSON, and calls `StudentCreate.from_dict(body)` to create the instance. Only keys declared in the schema (via type annotations) are accepted; extras are silently ignored.

**`Schema` methods:**

| Method | Description |
|---|---|
| `Schema(**kwargs)` | Constructor — sets attributes for all annotated fields present in `kwargs` |
| `instance.dict()` | Returns `{field: value, ...}` for every annotated field |
| `Schema.from_dict(data)` | Class method — constructs an instance from a plain dict, filtering to known fields |

Body parsing happens only for `POST`, `PUT`, and `PATCH` requests. `GET` and `DELETE` never read the body.

If the request body is not valid JSON, Rusjango returns:

```json
{"error": "Unprocessable Entity", "detail": "Invalid JSON: ...", "status": 422}
```

### Raw dict body

If the type annotation is `dict`, the parsed JSON object is passed through directly:

```python
@app.post("/items")
async def create_item(data: dict):
    return {"received": data}
```

### Body parameter resolution

The framework inspects the function signature after path and query parameters have been bound. The **first remaining unbound parameter** receives the body. If that parameter's annotation is a `Schema` subclass, `from_dict()` is called; otherwise the raw parsed value is passed.

---

## HTTP exceptions

Raise `HTTPException` from any handler to return a structured error response:

```python
from rusjango import HTTPException

@app.get("/secret")
async def secret():
    raise HTTPException(403, detail="Forbidden")
```

```python
# With custom headers
raise HTTPException(401, detail="Unauthorized", headers={"WWW-Authenticate": "Bearer"})
```

**`HTTPException` constructor:**

| Parameter | Type | Description |
|---|---|---|
| `status_code` | `int` | HTTP status code |
| `detail` | `Any` | Human-readable message or structured data (optional) |
| `headers` | `dict[str, str]` | Extra response headers (optional) |

---

## Response format

The framework maps handler return values to HTTP responses automatically:

| Return value | Status | Body |
|---|---|---|
| `dict` | `200 OK` | JSON-serialised dict |
| `list` | `200 OK` | JSON-serialised list |
| `None` | `204 No Content` | `{}` |
| `HTTPException` raised | exception's `status_code` | Error envelope (see below) |
| Unhandled exception (DEBUG=True) | `500` | Error envelope with full traceback |
| Unhandled exception (DEBUG=False) | `500` | Error envelope without traceback |

All responses use `Content-Type: application/json; charset=utf-8`.

### Error envelope

All error responses share the same JSON structure:

```json
{
  "error": "Not Found",
  "detail": "No route for GET /missing",
  "status": 404
}
```

| Key | Always present | Description |
|---|---|---|
| `"error"` | Yes | Short label derived from the status code |
| `"detail"` | No | The `detail` value from the `HTTPException`, or traceback string in debug mode |
| `"status"` | Yes | Numeric HTTP status code |

Status-to-label mapping used by the framework:

| Status | Label |
|---|---|
| 400 | Bad Request |
| 404 | Not Found |
| 405 | Method Not Allowed |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |
| *(other)* | Error |

---

## Per-app routers

Each app under `apps/` defines its own `Router` instance in `api.py`. `Router` is an alias for `Rusjango` — it has the same interface but carries only that app's routes:

```python
# apps/school/api.py
from rusjango import Router

router = Router()


@router.get("/students")
async def list_students():
    return [{"name": "Ali"}, {"name": "Sara"}]


@router.get("/students/{id}")
async def get_student(id: int):
    return {"id": id}


@router.post("/students")
async def create_student(data: dict):
    return {"created": data}
```

> **Important:** The variable must be named exactly `router` (lowercase). The `app.load_installed_apps()` mechanism looks for `api_module.router` by that name.

Do not import or use the module-level `router` singleton from `rusjango.router` inside app packages. That singleton is a convenience for tiny single-file scripts only. Multi-app projects must create a fresh `Router()` instance per app.

---

## Mounting routers

Routers are mounted programmatically via `include_router`:

```python
# main.py
from rusjango import Rusjango
from apps.school.api import router as school_router

app = Rusjango(settings="settings.py")

app.include_router(school_router, prefix="/api/school")
```

Every route in `school_router` has its path prefixed with `/api/school`. A route defined as `@router.get("/students")` becomes `/api/school/students`.

### Automatic mounting via `load_installed_apps`

Rather than manually calling `include_router` for each app, `app.load_installed_apps()` handles this automatically for every entry in `INSTALLED_APPS`:

```python
# main.py (generated)
app.load_installed_apps()
```

For each entry `"apps.<name>"` in `INSTALLED_APPS`:
1. `apps.<name>.api` is imported.
2. `api_module.router` is retrieved.
3. `app.include_router(router, prefix="/api/<name>")` is called.
4. If `DATABASE` is configured, `apps.<name>.models` is also imported to register model classes.

---

## Middleware

Middleware is configured in `settings.py`:

```python
MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",
    "myapp.middleware.LoggingMiddleware",
]
```

The list is processed such that the **first entry is the outermost layer** — it sees the request first and the response last.

### Built-in: `SecurityMiddleware`

`rusjango.security.SecurityMiddleware` is included by default in every generated project. It:

- Validates the `Host` header against `ALLOWED_HOSTS` when `DEBUG = False`. Requests with an unrecognised host are rejected with `400 Bad Request`.
- Appends `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY` to every response.

When `DEBUG = True`, host validation is skipped entirely so any host is accepted during development.

### Custom middleware

A custom middleware class must accept the downstream app in `__init__` and implement the ASGI `__call__` protocol:

```python
# myapp/middleware.py
import time

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.monotonic()
        method = scope["method"]
        path = scope["path"]

        await self.app(scope, receive, send)

        elapsed = (time.monotonic() - start) * 1000
        print(f"{method} {path}  {elapsed:.1f}ms")
```

Register it in `settings.py`:

```python
MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",
    "myapp.middleware.LoggingMiddleware",
]
```

The middleware import path must be a dotted string that resolves to the class (not the module).

### Middleware and settings access

`SecurityMiddleware` demonstrates how middleware can access settings: the `Rusjango` core stores settings in `scope["rusjango"]["settings"]` before invoking the middleware stack, so any middleware layer can read it:

```python
settings = scope.get("rusjango", {}).get("settings", {})
debug = settings.get("DEBUG", False)
```
