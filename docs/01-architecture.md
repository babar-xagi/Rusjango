# Architecture

Applies to Rusjango 0.1.4 (alpha).

## Repository

| Directory | Responsibility |
|---|---|
| `python/rusjango/src/rusjango` | Application, Python CLI, schemas, middleware, ORM |
| `python/rusjango/tests` | Runtime, CLI, regression, and PostgreSQL tests |
| `cli` | Standalone Rust CLI |
| `crates/rusjango-core` | PyO3 extension; version and placeholder route_count |
| `templates` | Templates embedded into the Rust binary |
| `examples/hello` | Sample school API |
| `scripts` | Distribution and disposable PostgreSQL validation |

## Request flow

```text
Uvicorn -> Rusjango.__call__ -> middleware -> route match
        -> bind path/query/body -> await handler -> JSON response
```

Settings are attached to the scope before middleware runs. Middleware is built lazily and cached. Routes are compiled at registration and matched in registration order; define specific routes before overlapping parameter routes.

Each installed app owns a fresh `Router()` and is mounted under `/api/<leaf_name>`. Repeated `load_installed_apps()` calls do not duplicate already mounted apps.

## Database lifecycle

DATABASE configures one process-wide backend. Connections open lazily on first use. `migrate` creates missing tables explicitly. ASGI shutdown closes connections; startup acknowledges the protocol without creating tables. Close the current database before changing its configuration.

SQLite statements are serialized on a shared connection; insert results are read on that connection before commit. PostgreSQL operations acquire and release pool connections. This is not a transaction API or support for independently configured databases in one process.

## Rust boundary

Request execution remains in Python. Rust currently supplies the CLI and a placeholder extension. Dependencies for future async Rust features are not included until those features are implemented.
