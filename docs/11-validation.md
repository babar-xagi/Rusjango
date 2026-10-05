# ✅ Validation record

**Rusjango 0.1.4 · Alpha**

Date: 2026-10-05. Release 0.1.4 was validated, published, and verified from PyPI. The release source is commit `2f2bc8bbb5223a58872b3b32a937867895a993e2`.

## 🧪 Local results

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

## 🔁 Reproduce the checks

Follow [contributing](10-contributing.md) for the source suite and disposable PostgreSQL runner. Build and exercise the installed artifact with:

```bash
uv build --package rusjango
.venv/bin/python scripts/verify_wheel.py dist/rusjango-0.1.4-cp311-abi3-linux_x86_64.whl
```

`uv build` creates the source archive first, then builds the wheel from that archive. Set `UV_PYTHON=3.14` to override the repository's Python 3.12 pin. Use an absolute PYO3_PYTHON path when running Cargo against a managed interpreter.

## 🌍 Hosted release results

- [Main CI](https://github.com/babar-xagi/Rusjango/actions/runs/37332329846): all 13 jobs passed, covering Python 3.11-3.14 on Linux, Windows, and macOS plus Rust, PostgreSQL, and distributions.
- [Release workflow](https://github.com/babar-xagi/Rusjango/actions/runs/37332756735): all 22 jobs passed, including repeated validation, tag checks, platform builds, metadata validation, PyPI upload, and GitHub release creation.
- [PyPI 0.1.4](https://pypi.org/project/rusjango/0.1.4/) contains five platform wheels and the source archive. Wheels cover Linux x86_64/aarch64, Windows x86_64, and macOS x86_64/arm64.
- [GitHub v0.1.4](https://github.com/babar-xagi/Rusjango/releases/tag/v0.1.4) points to the verified source and includes all six distribution files and release notes.
- Fresh installations directly from PyPI on Python 3.11 and 3.14 passed native import/version checks, generated-project scaffolding, migration, create/list requests, and a 422 validation response.

## 🧭 Scope of the evidence

- The full suite with both CLIs and live PostgreSQL ran on Linux. Windows/macOS source suites passed in CI; native wheels built successfully for all five platform targets.
- Fresh installed-wheel API checks were executed on Linux; these results do not imply native API smoke tests were executed on Windows/macOS.
- Tests do not establish production readiness, load limits, or a performance advantage.
- Existing databases affected by the old default table name require manual data migration; tests use isolated databases.
- Tracked migrations, transactions, relationships, auth, admin, OpenAPI, Docker scaffolding, and application test scaffolding remain pending.

## 📚 Documentation checks

The tutorial refresh was checked against published 0.1.4 in an isolated generated project:

- The uv quick start, app scaffolding, ORM activation, and migration commands completed successfully.
- README request/response examples, route/query/body examples, nested schemas, CRUD, and missing-row handling were executed successfully.
- All 24 Markdown files were checked for valid Python/JSON examples, local or repository-file links, complete code fences, and text encoding.

These are documentation checks. The release test counts above remain the recorded results for the release source.

The next phase gate is listed in [PROGRESS.md](../PROGRESS.md).

---

[📚 Documentation home](README.md)
