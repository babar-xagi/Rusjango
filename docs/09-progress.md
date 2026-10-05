# Phase tracking

Applies to Rusjango 0.1.4 (alpha).

[PROGRESS.md](../PROGRESS.md) is the maintained phase tracker. [Validation results](11-validation.md) record the latest local gate run.

## Implementation map

- Phase 1: app.py, routing.py, asgi.py, middleware.py, security.py, server.py, cli.py, cli/src.
- Phase 2: apps.py, per-app Router instances, both CLI app commands, templates/app.
- Phase 3: orm/fields.py, model.py, query.py, sql.py, connection.py, _migrate.py, templates/orm.
- Phase 4 foundation: schema.py and request-validation dispatch in routing.py.

Phases 1–3 being implemented does not mean production readiness. ORM schema evolution, transactions, relationships, request limits, and operational hardening remain gaps. Rust request acceleration is not yet implemented.
