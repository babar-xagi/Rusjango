# 🧭 Implementation progress

**Rusjango 0.1.5 · Alpha**

[PROGRESS.md](../PROGRESS.md) is the maintained phase tracker. Use this page to connect implemented behavior to its source files.

## ✅ Implemented foundations

| Phase | Scope | Main implementation |
|---|---|---|
| 1 | CLI, async JSON routes, parameters, middleware, lifecycle | `app.py`, `routing.py`, `asgi.py`, `middleware.py`, `security.py`, `server.py`, CLI |
| 2 | Add/remove apps and independent route mounting | `apps.py`, `Router`, app commands, `templates/app` |
| 3 | SQLite/PostgreSQL CRUD and missing-table creation | `orm/`, `_migrate.py`, `templates/orm` |
| 4 | Coercion, constraints, validators, Docker/test scaffolding | `schema.py`, `scaffolding.py`, shared templates, both CLIs |

The [0.1.5 release notes](releases/0.1.5.md) summarize Phase 4. The [Phase 4 validation record](16-phase4-validation.md) records its checks; the [0.1.4 record](11-validation.md) preserves earlier evidence.

## ✅ Phase 4

Phase 4 implements opt-in coercion, Field constraints, synchronous field/model validators, and add/remove Docker/test scaffolding in both CLIs. Generated files are tracked and user edits are preserved.

Relationships, tracked migrations, and transactions remain separate ORM work. Auth should be established before an admin interface is exposed.

## 🧪 Readiness and performance

Implemented phases are feature milestones. They do not establish production readiness or a performance advantage.

Operational gaps include request limits and broader hardening. Rust request acceleration remains planned.

---

[📚 Documentation home](README.md) · [Full phase tracker →](../PROGRESS.md)
