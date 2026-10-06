# 🧭 Build progress

Updated 2026-10-06. Feature milestones are separate from production-readiness claims.

Version 0.1.5 completes Phase 4 and is published on [PyPI](https://pypi.org/project/rusjango/0.1.5/) with a [GitHub release](https://github.com/babar-xagi/Rusjango/releases/tag/v0.1.5). All 13 main CI jobs and 22 release jobs passed. See [release notes](docs/releases/0.1.5.md) and the [Phase 4 validation record](docs/16-phase4-validation.md). Earlier [0.1.4 validation](docs/11-validation.md) remains available.

| Phase | Scope | Status |
|---|---|---|
| 1 | Minimal CLI, async JSON API, routing, middleware | Implemented and regression-tested |
| 2 | Add/remove apps, isolated route mounting | Implemented in both CLIs |
| 3 | SQLite/PostgreSQL CRUD and table creation | Foundation implemented and integration-tested |
| 4 | Validation extensions, Docker/test scaffolding | Complete; runtime/package/container/release gates passed |
| 5 | Admin | Next: groundwork; public endpoints require auth first |
| 6 | Auth and permissions | Planned; prerequisite for exposing admin |
| 7 | OpenAPI and developer experience | Tutorials available; API documentation generation pending |
| 8 | Background workers | Planned |
| 9 | AI helpers | Planned |
| 10 | Enterprise capabilities | Planned |

## ✅ Phase 4 implementation

- Strict validation remains the default; controlled coercion is explicitly enabled per schema.
- Field supports numeric ranges, lengths, patterns, and independent defaults.
- Field validators transform values and preserve declared types; validate() checks cross-field relationships.
- Union validation preserves exact types, nested locations, finite floats, and distinct dictionary keys.
- Both CLIs add/remove Docker and test scaffolds from shared templates.
- Existing files, modified generated files, and unrelated settings/dependencies are preserved.
- Production container settings disable DEBUG and require allowed hosts.
- Generated test fixtures use in-memory SQLite and preserve application database files.
- Packaged templates and generated Docker behavior are checked in distribution/CI gates.

## 🧪 Gate before the next phase

Run both Python versions, both CLIs, real PostgreSQL, Rust formatting/tests/clippy, Python lint, clean wheel/source builds, generated tests, and Docker runtime/persistence checks. See [contributing](docs/10-contributing.md) and the [validation record](docs/16-phase4-validation.md).

## 🔜 Next: Phase 5

Define admin discovery, model views, and configuration interfaces. Establish authentication/permissions before exposing admin endpoints. Relationships, transactions, and tracked migrations remain separate ORM work.

The Rust request core is still a placeholder. Auth, admin, OpenAPI, workers, and enterprise behavior are not implemented.
