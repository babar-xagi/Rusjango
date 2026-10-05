# Phase 1–3 validation record

Applies to Rusjango 0.1.4 (alpha).

Date: 2026-10-05. This record describes local validation of the 0.1.4 release candidate. Hosted results are recorded separately after the workflow completes.

## Local results

Executed in WSL2 Ubuntu against `/mnt/d/Rusjango`:

Toolchain: Rust/Cargo 1.99.0, PyO3 0.29.3, and SQLite 3.53.1 on the Python 3.14 environment.

| Check | Result |
|---|---|
| Full Python suite on Python 3.11.16 | 74 passed; no skips |
| Full Python suite on Python 3.14.7 | 74 passed; no skips |
| Rust workspace tests | 4 passed |
| Rust formatting and clippy with warnings denied | Passed |
| Python formatting and Ruff undefined/unused-code checks | Passed |
| Source distribution | Built successfully |
| Wheel rebuilt from extracted source distribution | Built successfully |
| Fresh installed-wheel smoke tests on Python 3.11 and 3.14 | Passed |

Both full Python runs included the compiled Rust CLI, the Python CLI, SQLite, and a disposable live PostgreSQL server. Tests cover concurrent inserts, affected-row counts, constraint failures, pool reuse, safe settings edits, custom API preservation, generated-project migration, schema validation, routing errors, production hosts, and a real Uvicorn lifespan/HTTP exchange.

Rust's four unit tests cover embedded templates and literal settings edits. The native runtime is still a placeholder; these results establish packaging and CLI correctness, not runtime acceleration.

The wheel smoke test uses a fresh virtual environment outside the checkout with PYTHONPATH removed. It imports the native module, compares package/native versions, generates a project, enables ORM, creates tables, performs create/list requests, and checks a 422 validation response.

## Reproduce

Follow [contributing](10-contributing.md) for the source suite and disposable PostgreSQL runner. Build and exercise the installed artifact with:

```bash
uv build --package rusjango
.venv/bin/python scripts/verify_wheel.py dist/rusjango-0.1.4-cp311-abi3-linux_x86_64.whl
```

`uv build` creates the source archive first, then builds the wheel from that archive. Set `UV_PYTHON=3.14` to override the repository's Python 3.12 pin. Use an absolute PYO3_PYTHON path when running Cargo against a managed interpreter.

## Boundaries

- Windows/macOS and Python 3.12/3.13 checks are configured in CI; the complete final suite was run locally on Linux with Python 3.11 and 3.14.
- Hosted CI and release publication are separate gates; local results do not imply those jobs have completed.
- Tests do not establish production readiness, load limits, or a performance advantage.
- Existing databases affected by the old default table name require manual data migration; tests use isolated databases.
- Tracked migrations, transactions, relationships, auth, admin, OpenAPI, Docker scaffolding, and application test scaffolding remain pending.

The next phase gate is listed in [PROGRESS.md](../PROGRESS.md).
