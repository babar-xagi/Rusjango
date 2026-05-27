# Python Layer Internals

This document explains how the core Python modules in `python/rusjango/src/rusjango/` are designed and how they interact at runtime.

---

## ASGI compliance

Rusjango is a fully compliant **ASGI 3.0** application. Any ASGI-compatible server can run it:

```bash
uvicorn asgi:app --reload      # development
hypercorn asgi:app             # alternative server
daphne asgi:app                # Django Channels server
```

The ASGI entry point is the `RusjangoApp.__call__` method:

```python
class RusjangoApp:
    async def __call__(
        self,
        scope: dict,
        receive: Callable,
        send: Callable,
    ) -> None:
        ...
```

`scope` is a dict describing the connection. Key fields for HTTP requests:

| Key | Type | Example |
|---|---|---|
| `type` | `str` | `"http"` |
| `method` | `str` | `"GET"` |
| `path` | `str` | `"/students/42"` |
| `query_string` | `bytes` | `b"page=2"` |
| `headers` | `list[tuple[bytes, bytes]]` | `[(b"host", b"localhost")]` |

`receive` is called to read request body chunks. `send` is called to write the response status line, headers, and body.

### Lifespan events

The framework also handles ASGI `lifespan` scope events:

```
startup  → init_db() is called if DATABASE is configured
shutdown → close_db() is called
```

This ensures the database connection is opened before the first request and cleanly closed when the server stops.

---

## Routing system (`routing.py`)

### Route compilation

Routes are compiled when they are **registered** (at import time), not on each request. The `{param}` URL syntax is converted to a named capture group regex:

```python
# Registration:
@router.get("/students/{id}")
async def get_student(id: int): ...

# Compiled internally to:
# pattern = "/students/{id}"
# regex   = re.compile(r"^/students/(?P<id>[^/]+)$")
# param_names = ["id"]
```

The `Route` dataclass is frozen (immutable after creation):

```python
@dataclass(frozen=True)
class Route:
    method:      str
    pattern:     str
    handler:     Callable
    regex:       re.Pattern
    param_names: tuple[str, ...]
```

### Request dispatch

When a request arrives, `Router.dispatch` iterates registered routes in registration order and tests the regex against the request path:

```python
for route in self.routes:
    if route.method == method:
        match = route.regex.match(path)
        if match:
            path_params = match.groupdict()
            return await call_handler(route.handler, path_params, query_params, body)
raise NotFound()
```

### Handler introspection (`call_handler`)

`call_handler` inspects the handler's function signature using `inspect.signature` and `typing.get_type_hints` to determine how each parameter should be sourced:

```
Parameter source resolution order:
  1. Path params   — name is in path_params dict
  2. Query params  — name is in query_params dict
  3. Schema body   — type hint is a Schema subclass
  4. (future)      — request object, auth user, etc.
```

Type coercion for path and query params is applied using the declared type hint:

```python
hint = hints.get(param_name)
if hint is int:
    value = int(raw_value)
elif hint is float:
    value = float(raw_value)
else:
    value = raw_value   # str by default
```

---

## ORM design (`orm/`)

See `docs/internals/orm-internals.md` for a deep dive. Summary of the layered design:

```
orm/
  __init__.py    ← public exports: Model, Field types, init_db, close_db
  model.py       ← ModelMeta metaclass; Model base class; _MODEL_REGISTRY
  fields.py      ← Field base class; IntField, CharField, BoolField, etc.
  queryset.py    ← lazy QuerySet; defers SQL until terminal method
  sql.py         ← pure SQL string generation (no DB calls)
  connection.py  ← connection lifecycle; acquire() context manager
```

The separation between `sql.py` (SQL generation) and `connection.py` (execution) means SQL generation can be tested in isolation without a database.

---

## Middleware stack (`middleware.py`)

`build_middleware_stack` is called once at application startup:

```python
def build_middleware_stack(
    core_app: Callable,
    middleware_paths: list[str],
) -> Callable:
    app = core_app
    for dotted_path in reversed(middleware_paths):
        cls = import_from_string(dotted_path)
        app = cls(app)
    return app
```

The returned `app` is the outermost callable. When a request arrives, it passes through every middleware layer before reaching the core ASGI handler.

### `import_from_string`

A small utility that resolves dotted Python paths to class objects at runtime:

```python
def import_from_string(dotted: str) -> type:
    module_path, cls_name = dotted.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, cls_name)
```

This is how `"rusjango.security.SecurityMiddleware"` becomes the actual `SecurityMiddleware` class.

---

## Settings isolation

Settings are loaded **once** at startup by `load_settings` and stored as a plain `dict`. They are never stored in a module-level global that's readable across the process — instead, they are injected into the ASGI scope on every request:

```python
# Inside the core ASGI handler, before dispatching:
scope.setdefault("rusjango", {})
scope["rusjango"]["settings"] = self._settings
```

**Benefits of this design:**

- **No global state** — multiple `RusjangoApp` instances can have different settings in the same process (useful for testing).
- **No import-time side effects** — nothing happens just by importing `rusjango`; settings only take effect when an app instance is created and started.
- **Predictable for tests** — tests can create an app with a custom settings dict without monkey-patching globals.

### Accessing settings anywhere in the stack

Middleware, route handlers (via `scope`), and the ORM startup hook all read from the same injected dict:

```python
# In middleware:
settings = scope["rusjango"]["settings"]

# In a route handler (if scope is passed explicitly):
async def my_handler(scope: dict) -> dict:
    settings = scope["rusjango"]["settings"]
    debug = settings.get("DEBUG", False)
```

---

## Error handling (`exceptions.py`)

All HTTP errors inherit from `HttpException`:

```python
class HttpException(Exception):
    status_code: int
    detail: str
```

Built-in subclasses:

| Class | Status |
|---|---|
| `BadRequest` | 400 |
| `Unauthorized` | 401 |
| `Forbidden` | 403 |
| `NotFound` | 404 |
| `MethodNotAllowed` | 405 |
| `InternalServerError` | 500 |

When an `HttpException` is raised inside a route handler, the core ASGI handler catches it and returns the appropriate JSON response:

```json
{"error": "Not Found"}
```

Unhandled exceptions (any non-`HttpException`) become `500` responses. If `DEBUG=True`, the response also includes `"traceback"` with the full Python traceback string.

---

## App loading (`apps.py`)

When the `RusjangoApp` starts, it calls `load_apps(installed_apps)` which:

1. Iterates `INSTALLED_APPS`.
2. Imports `<app_package>.api`.
3. Reads `router` from the module.
4. Mounts the router at `/api/<leaf_name>/`.

```python
def load_apps(installed_apps: list[str]) -> list[tuple[str, Router]]:
    result = []
    for app_path in installed_apps:
        module = importlib.import_module(f"{app_path}.api")
        router = getattr(module, "router")
        leaf   = app_path.split(".")[-1]
        result.append((f"/api/{leaf}", router))
    return result
```

The prefix `/api/<leaf>` is prepended to every route pattern in the mounted router. A route registered as `@router.get("/students")` inside `apps.school` becomes `/api/school/students`.
