# 🧭 Build progress

Updated 2026-10-06. Feature milestones are separate from production-readiness claims.

Version 0.1.6 implements Phase 5 admin foundations. Local runtime, both-CLI, PostgreSQL, Rust, distribution, installed-wheel, and Docker persistence checks passed. See [release notes](docs/releases/0.1.6.md) and the [Phase 5 validation record](docs/18-phase5-validation.md). Earlier [Phase 4](docs/16-phase4-validation.md) and [0.1.4 validation](docs/11-validation.md) records remain available.

| Phase | Scope | Status |
|---|---|---|
| 1 | Minimal CLI, async JSON API, routing, middleware | Implemented and regression-tested |
| 2 | Add/remove apps, isolated route mounting | Implemented in both CLIs |
| 3 | SQLite/PostgreSQL CRUD and table creation | Foundation implemented and integration-tested |
| 4 | Validation extensions, Docker/test scaffolding | Complete; runtime/package/container/release gates passed |
| 5 | Admin | Backend groundwork complete; HTTP dashboard awaits auth |
| 6 | Auth and permissions | Next: trusted identity integration before exposing admin |
| 7 | OpenAPI and developer experience | Tutorials available; API documentation generation pending |
| 8 | Background workers | Planned |
| 9 | AI helpers | Planned |
| 10 | Enterprise capabilities | Planned |

## ✅ Phase 5 implementation

- Independent AdminSite registries and synchronous per-application factory loading.
- Optional installed-app discovery with repeat-load protection and rollback on registration failure.
- Explicit visible fields, bounded pagination, typed filters, stable sorting, and literal search.
- Exact per-model grants checked before database access.
- Read-only defaults; typed create/update schemas and separately enabled deletion.
- Protected primary keys, rejected unknown writes, and form metadata without private default values.
- Shared Python/Rust admin scaffold with conflict checks and preservation of edits.
- SQLite/PostgreSQL regressions, fresh installed-wheel checks, and Docker discovery/persistence verification.

## 🧪 Gate before the next phase

Run both Python versions, both CLIs, real PostgreSQL, Rust formatting/tests/clippy, Python lint, clean wheel/source builds, generated tests, and Docker runtime/persistence checks. See [contributing](docs/10-contributing.md) and the [validation record](docs/18-phase5-validation.md).

## 🔜 Next: Phase 6

Implement authentication and connect verified identities to permissions before exposing browser admin routes. Model-level grants are groundwork; sessions/tokens, CSRF and the HTTP authorization boundary remain to be designed and tested.

Relationships, transactions, and tracked migrations remain separate ORM work. The Rust request core is still a placeholder. OpenAPI, workers, and enterprise behavior remain pending.
