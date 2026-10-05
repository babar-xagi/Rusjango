# Build progress

Updated 2026-10-05. This file records implemented scope and the gate for the next phase. Feature plans are not production-readiness claims.

Version 0.1.4 packages the Phase 1–3 repair pass. See the [release notes](docs/releases/0.1.4.md), [validation record](docs/11-validation.md), and [release procedure](docs/12-releasing.md).

| Phase | Scope | Status |
|---|---|---|
| 1 | Minimal CLI, async JSON API, routing, middleware | Implemented; regression fixes added |
| 2 | Add/remove apps, isolated route mounting | Implemented; both CLIs tested |
| 3 | SQLite/PostgreSQL CRUD and table creation | Foundation implemented; regression and integration tests added |
| 4 | Expanded validation, Docker and test scaffolding | Partial: strict schemas/defaults/nesting implemented; coercion policy, validators and scaffolding pending |
| 5 | Admin | Planned |
| 6 | Auth and permissions | Planned |
| 7 | OpenAPI and developer experience | Written docs available; API documentation generation pending |
| 8 | Background workers | Planned |
| 9 | AI helpers | Planned |
| 10 | Enterprise capabilities | Planned |

## Phase 1–3 repair pass

- Literal route matching, 405 responses with Allow, 422 input errors, and empty 204 bodies.
- Settings available before middleware; host checks and headers also cover rejected requests.
- Lifespan startup/shutdown acknowledgements and database shutdown cleanup.
- Per-model table names, atomic insert results, null filters, and real affected-row counts.
- PostgreSQL identity keys, corrected update parameters, pooled connection release, and live-backend tests.
- Scaffolding preserves custom APIs and unrelated settings; migration subprocess failures propagate.
- Rust templates embedded in the binary; Python/Rust versions aligned at 0.1.4.
- Source install and distribution validation; CI covers regression tests and PostgreSQL.

## Gate before Phase 4 expansion

Run the Python suite, Rust CLI integration tests, real PostgreSQL tests, Rust formatting/clippy, Python lint, and wheel/source-distribution checks. See [contributing](docs/10-contributing.md) for commands and [validation](docs/11-validation.md) for the last local results.

## Next: Phase 4

1. Decide and document opt-in coercion and validation extension APIs.
2. Implement Docker scaffolding with a production configuration example.
3. Implement application test scaffolding.
4. Test feature add/remove behavior and document every new command.

Keep auth ahead of exposing an admin interface. Relationships, tracked migrations, and transaction support remain separate ORM work; `migrate` currently creates tables only.
