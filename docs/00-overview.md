# Overview

Applies to Rusjango 0.1.4 (alpha).

Rusjango is an alpha API framework for developers who want a small async Python application organized into Django-style app packages.

A project begins with three files. `add app` creates a router package; `add orm` configures SQLite and adds starter model/schema files. The Python package contains the full CLI. The Rust CLI offers the same commands and embeds its templates at build time.

The runtime currently uses Uvicorn, Python routing/middleware/JSON serialization, and aiosqlite or asyncpg. The PyO3 Rust extension establishes a future integration boundary, but does not accelerate requests today.

## Implemented scope

Routing, typed primitive parameters, strict schemas, middleware, app mounting, basic async CRUD, and table creation. Admin, auth, OpenAPI, workers, AI integrations, and enterprise features are plans.

## Product direction

The distinguishing goal is reliable progressive scaffolding: adding a feature should preserve the developer's existing code. No benchmark or user-adoption evidence currently proves a performance or ecosystem advantage.

Use it for experimentation and contribution. Review the [current limitations](../README.md#current-limits) before choosing it for an application. See [progress](../PROGRESS.md) for phase boundaries.
