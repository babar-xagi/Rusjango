# 🧭 Implementation progress

**Rusjango 0.1.4 · Alpha**

[PROGRESS.md](../PROGRESS.md) is the maintained phase tracker. Use this page to connect implemented behavior to its source files.

## ✅ Implemented foundations

| Phase | Scope | Main implementation |
|---|---|---|
| 1 | CLI, async JSON routes, parameters, middleware, lifecycle | `app.py`, `routing.py`, `asgi.py`, `middleware.py`, `security.py`, `server.py`, CLI |
| 2 | Add/remove apps and independent route mounting | `apps.py`, `Router`, app commands, `templates/app` |
| 3 | SQLite/PostgreSQL CRUD and missing-table creation | `orm/`, `_migrate.py`, `templates/orm` |
| 4 foundation | Strict types, defaults, nesting, and collections | `schema.py` and request validation in `routing.py` |

The [0.1.4 release notes](releases/0.1.4.md) summarize the repair pass. The [validation record](11-validation.md) links to the successful local and hosted checks.

## 🔜 Next phase

Phase 4 still needs a documented coercion/validator extension API, Docker scaffolding, and application test scaffolding.

Relationships, tracked migrations, and transactions remain separate ORM work. Auth should be established before an admin interface is exposed.

## 🧪 Readiness and performance

Implemented phases are feature milestones. They do not establish production readiness or a performance advantage.

Operational gaps include request limits and broader hardening. Rust request acceleration remains planned.

---

[📚 Documentation home](README.md) · [Full phase tracker →](../PROGRESS.md)
