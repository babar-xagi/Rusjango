# 🛡️ Middleware and host checks

**Rusjango 0.1.4 · Alpha**

Middleware wraps an ASGI application to inspect requests or responses. Configure it with dotted class paths in `settings.py`.

## 🔗 Understand the order

```python
MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",
    "middleware.LoggingMiddleware",
]
```

The first entry sees the request first and the response last:

```text
Request  → Security → Logging → Route
Response ← Security ← Logging ← Route
```

## ✍️ Write a middleware class

Create `middleware.py` beside `main.py`:

```python
class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            settings = scope.get("rusjango", {}).get("settings", {})
            print(settings.get("APP_NAME"), scope["method"], scope["path"])

        await self.app(scope, receive, send)
```

Register it with the setting above. Rusjango attaches application settings to the scope before middleware runs.

Keep mutable middleware state safe when requests run concurrently.

## 📤 Add a response header

A middleware can wrap `send`:

```python
class ResponseHeaderMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def send_with_header(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-app", b"rusjango"))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_header)
```

Register `"middleware.ResponseHeaderMiddleware"` to enable it. ASGI headers are byte pairs.

## 🔒 Use SecurityMiddleware

```python
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",
]
```

A missing, malformed, or disallowed Host header returns **400**. Valid allowed hosts continue to the route.

The middleware adds these headers, including on rejected-host responses and errors produced by the core HTTP handler:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |

With `DEBUG = True`, host checks are skipped. Read the [settings guide](06-settings-reference.md) for domain and IPv6 patterns.

## 🔄 Startup and shutdown

Rusjango handles ASGI lifespan directly, outside the HTTP middleware stack.

- Startup configures the backend and acknowledges startup.
- Connections are opened lazily on use.
- Shutdown closes the configured database and acknowledges shutdown.
- Startup does not create tables; run `migrate` explicitly.

Custom HTTP middleware is not a startup-hook API.

## 🧭 Current boundaries

Built-in auth, CORS, CSRF, sessions, rate limiting, and HTTPS redirection are pending. SecurityMiddleware supplies the documented host check and response headers.

---

[← Settings](06-settings-reference.md) · [📚 Documentation home](README.md) · [CLI reference →](03-cli-reference.md)
