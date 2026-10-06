# 🧭 Implementation progress

**Rusjango 0.1.6 · Alpha**

[PROGRESS.md](../PROGRESS.md) is the maintained phase tracker. Use this page to connect implemented behavior to its source files.

## ✅ Implemented foundations

| Phase | Scope | Main implementation |
|---|---|---|
| 1 | CLI, async JSON routes, parameters, middleware, lifecycle | `app.py`, `routing.py`, `asgi.py`, `middleware.py`, `security.py`, `server.py`, CLI |
| 2 | Add/remove apps and independent route mounting | `apps.py`, `Router`, app commands, `templates/app` |
| 3 | SQLite/PostgreSQL CRUD and missing-table creation | `orm/`, `_migrate.py`, `templates/orm` |
| 4 | Coercion, constraints, validators, Docker/test scaffolding | `schema.py`, `scaffolding.py`, shared templates, both CLIs |
| 5 | Admin registry, discovery, permission-gated data and typed writes | `admin.py`, `app.py`, `apps.py`, admin template, both CLIs |

The [0.1.6 release notes](releases/0.1.6.md) summarize Phase 5 foundations. The [Phase 5 validation record](18-phase5-validation.md) records its checks; [Phase 4](16-phase4-validation.md) and [0.1.4](11-validation.md) preserve earlier evidence.

## ✅ Phase 4

Phase 4 implements opt-in coercion, Field constraints, synchronous field/model validators, and add/remove Docker/test scaffolding in both CLIs. Generated files are tracked and user edits are preserved.

Relationships, tracked migrations, and transactions remain separate ORM work. Auth should be established before an admin interface is exposed.

## 🛡️ Phase 5 and next steps

Phase 5 provides a server-side registry, optional app discovery, explicit visible fields, bounded data views, exact grants, and optional schema-validated writes. No HTTP admin routes are installed.

Phase 6 will establish authentication and connect verified identities to these permissions before browser exposure. The [admin tutorial](17-admin.md) explains the current trusted-server boundary.

## 🧪 Readiness and performance

Implemented phases are feature milestones. They do not establish production readiness or a performance advantage.

Operational gaps include request limits and broader hardening. Rust request acceleration remains planned.

---

[📚 Documentation home](README.md) · [Full phase tracker →](../PROGRESS.md)
