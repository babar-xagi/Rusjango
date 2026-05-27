# Middleware

Middleware in Rusjango follows the standard ASGI middleware pattern: each class wraps the application and intercepts requests before they reach route handlers, and responses before they are sent back to the client.

---

## How middleware works

Every middleware class receives the inner ASGI application in `__init__` and implements `__call__` with the standard ASGI signature:

```
scope  →  dict describing the connection (type, method, path, headers, …)
receive →  async callable to read incoming body chunks
send   →  async callable to write response parts
```

The full chain is assembled once at startup by `build_middleware_stack` in `middleware.py`:

```python
# middleware.py (simplified)
def build_middleware_stack(core_app, middleware_paths: list[str]):
    app = core_app
    for path in reversed(middleware_paths):
        cls = import_string(path)
        app = cls(app)
    return app
```

Because the list is **reversed before wrapping**, the last entry in `MIDDLEWARE` ends up as the outermost layer — the first to see an incoming request. This matches Django's convention.

```
MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",   # ← inner (runs second)
    "myapp.middleware.LoggingMiddleware",      # ← outer (runs first)
]

Request flow:
  Client → LoggingMiddleware → SecurityMiddleware → Core handler → response
```

---

## Built-in middleware

### `rusjango.security.SecurityMiddleware`

Included in every new project by default.

**Responsibilities:**

1. **Host validation** — When `DEBUG=False`, validates the `Host` request header against `ALLOWED_HOSTS`. Requests with an unrecognised host receive:
   ```json
   {"error": "Invalid Host header"}
   ```
   with HTTP status `400 Bad Request`.

2. **Security headers** — Appends the following headers to every response:

   | Header | Value | Purpose |
   |---|---|---|
   | `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing |
   | `X-Frame-Options` | `DENY` | Disallows embedding in iframes |

Host validation is **skipped** when `DEBUG=True` to avoid friction during local development.

---

## Writing a custom middleware

Any class that implements the ASGI interface can be registered as middleware.

```python
# myapp/middleware.py
from __future__ import annotations

from typing import Any


class LoggingMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            print(f"{scope['method']} {scope['path']}")
        await self.app(scope, receive, send)
```

Register it in `settings.py`:

```python
MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",
    "myapp.middleware.LoggingMiddleware",
]
```

### Intercepting responses

To modify or inspect the outgoing response, wrap the `send` callable:

```python
class TimingMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        import time

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()

        async def send_with_timing(message: dict) -> None:
            if message["type"] == "http.response.start":
                elapsed = time.perf_counter() - start
                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-response-time", f"{elapsed:.4f}s".encode())
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_timing)
```

---

## Middleware execution order

Given this `MIDDLEWARE` list:

```python
MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",
    "myapp.middleware.TimingMiddleware",
    "myapp.middleware.LoggingMiddleware",
]
```

The stack is built by reversing the list and wrapping outward:

```
build order (reversed):
  1. core_app
  2. LoggingMiddleware(core_app)          # last in list → outermost
  3. TimingMiddleware(LoggingMiddleware)
  4. SecurityMiddleware(TimingMiddleware) # first in list → innermost

Request traversal:
  Client
    → LoggingMiddleware.__call__
      → TimingMiddleware.__call__
        → SecurityMiddleware.__call__
          → Core handler
        ← SecurityMiddleware (response)
      ← TimingMiddleware (adds header)
    ← LoggingMiddleware
  Client
```

---

## Accessing settings inside middleware

Settings are injected into the ASGI scope by the core handler before calling the middleware chain. They are available as:

```python
async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
    settings = scope.get("rusjango", {}).get("settings", {})
    debug    = settings.get("DEBUG", False)
    allowed  = settings.get("ALLOWED_HOSTS", ["*"])
    ...
```

This means middleware never needs to import a global settings object — configuration is passed through the scope, allowing multiple Rusjango instances with different settings to run in the same process.

---

## Middleware checklist

When writing custom middleware:

- [ ] Always pass non-HTTP scopes (e.g. `lifespan`) straight through without modification.
- [ ] Never swallow exceptions silently — let them propagate so the error handler can format them.
- [ ] Keep `__init__` lightweight; avoid I/O or blocking calls there.
- [ ] If your middleware holds shared state, make sure it is safe for concurrent async access.
