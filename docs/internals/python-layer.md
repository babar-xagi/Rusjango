# 🐍 Python runtime internals

**Rusjango 0.1.6 · Alpha**

This page connects the public API to the implementation. For usage examples, start with [Routes and requests](../04-api-design.md).

## 📁 Modules to explore

| Module | Responsibility |
|---|---|
| [app.py](../../python/rusjango/src/rusjango/app.py) | Application object, route registration, dispatch, and lifespan |
| [routing.py](../../python/rusjango/src/rusjango/routing.py) | Route compilation and handler argument binding |
| [schema.py](../../python/rusjango/src/rusjango/schema.py) | Strict field validation and schema serialization |
| [asgi.py](../../python/rusjango/src/rusjango/asgi.py) | Request body parsing and JSON/error responses |
| [apps.py](../../python/rusjango/src/rusjango/apps.py) | Installed-app imports and mounting |
| [cli.py](../../python/rusjango/src/rusjango/cli.py) | Python command implementations |
| [admin.py](../../python/rusjango/src/rusjango/admin.py) | Explicit model registry, trusted identity grants, projected data services |

## 🌐 Dispatch

1. `__call__` attaches application settings to the scope.
2. HTTP requests enter the lazily cached middleware stack.
3. The core matches a route and extracts path/query data.
4. `call_handler` resolves type hints, binds arguments, validates the body, and checks required inputs.
5. The handler runs asynchronously and its result is serialized.

Routes use escaped literals and named captures. Matching follows registration order. Signature and type-hint inspection currently occurs per request.

## 📥 Bodies and responses

Request chunks are buffered before JSON parsing. There is no request-size limit or streaming response API.

A `None` result sends empty 204 output. Serialization uses `json.dumps(default=str)`; return annotations do not enforce response schemas.

Lifespan startup/shutdown is handled outside HTTP middleware. Unsupported WebSocket connections are closed.

## 🧩 Apps and settings

`Router` is an alias for `Rusjango`, used to create independent app route tables. The exported singleton remains a single-file convenience.

`load_settings` executes a trusted Python file and extracts uppercase names. Settings belong to the application instance; database configuration and the model registry are process-wide.

`load_installed_apps` imports each API router, mounts it under `/api/<leaf>`, and imports models when configured. It tracks mounted packages to avoid duplicate routes. Missing model modules can be skipped; missing dependencies inside a model module propagate.

## 🛡️ Admin loading

`load_admin` resolves the configured synchronous factory and validates that it returns an AdminSite. The site belongs to the application instance. Installed-app callbacks are discovered once after successful registration, and their registry changes roll back on failure.

Service calls check exact model grants before queries, validate whitelisted inputs, and select only configured columns. Write schemas define allowed mutation fields; primary keys and unknown fields are rejected. This is a trusted server API with no HTTP routing or identity verification.

See the [admin tutorial](../17-admin.md) for the public interface.

## ✍️ CLI settings edits

The Python CLI uses AST locations and literal evaluation. It does not execute settings to mutate them.

Edited-value formatting and comments may change. Unrelated file contents are preserved.

---

[📚 Documentation home](../README.md) · [Architecture](../01-architecture.md) · [ORM internals →](orm-internals.md)
