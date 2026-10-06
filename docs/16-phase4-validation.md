# ✅ Phase 4 validation

**Rusjango 0.1.5 · Alpha**

Date: 2026-10-06. Phase 4 is published as 0.1.5 from verified source commit `e632fca`.

## 🧪 Local checks

- Full suite: 122 passed on Python 3.11.16 and 122 passed on Python 3.14.7 with both CLIs and a disposable live PostgreSQL backend.
- Rust workspace tests, formatting, and clippy passed.
- Python formatting and undefined/unused-code lint passed.
- Source distribution rebuilt successfully into a wheel.
- Fresh installed-wheel checks passed on Python 3.11 and 3.14, including Field/coercion/validator APIs, packaged Docker/test templates, generated pytest execution, and feature removal.
- The generated image built locally and passed host rejection, debug-off errors, explicit migration, CRUD, and nonroot UID checks.
- The restart smoke check was corrected to refresh Docker's dynamic port; its local rerun hit Docker Hub DNS timeout. Hosted Docker verification subsequently passed, including restart and persisted database data.

## 🔁 Reproduce

```bash
uv sync --all-packages --all-extras
cargo build -p rusjango-cli
RUSJANGO_RUST_CLI="$(pwd)/target/debug/rusjango" \
  .venv-postgres/bin/python scripts/test_postgres.py .venv/bin/python
uv build --package rusjango
.venv/bin/python scripts/verify_wheel.py dist/rusjango-0.1.5-cp311-abi3-linux_x86_64.whl
.venv/bin/python scripts/verify_docker.py dist/rusjango-0.1.5-cp311-abi3-linux_x86_64.whl
```

The PostgreSQL helper setup is explained in [contributing](10-contributing.md). Docker checks use uniquely named temporary projects and volumes, and clean up their own resources.

## 🌍 Hosted gates

- [Main CI](https://github.com/babar-xagi/Rusjango/actions/runs/37438434385): all 13 jobs passed, including the OS/Python matrix, both CLIs, live PostgreSQL, Rust, packages, and Docker build/runtime/persistence.
- [Release workflow](https://github.com/babar-xagi/Rusjango/actions/runs/37439320797): all 22 jobs passed, including repeated validation, all five platform builds, source distribution, metadata checks, PyPI publication, and GitHub release creation.
- [PyPI 0.1.5](https://pypi.org/project/rusjango/0.1.5/) contains five platform wheels and the source archive. The [GitHub release](https://github.com/babar-xagi/Rusjango/releases/tag/v0.1.5) includes the distribution artifacts and notes.
- Fresh PyPI installation on Python 3.14 passed native version checks, Field/coercion/validator behavior, both new scaffold types, migration, CRUD/422 responses, generated pytest execution, and feature removal.

## 🧭 Boundaries

Generated application tests use SQLite and direct ASGI calls. They do not establish PostgreSQL-specific behavior or network/lifespan behavior. The separate backend and container gates cover those concerns.

Nonroot containers and validation do not establish production readiness, throughput, auth, TLS termination, or request-size limits. The native Rust runtime remains a placeholder.

---

[📚 Documentation home](README.md) · [Phase 4 release notes](releases/0.1.5.md)
