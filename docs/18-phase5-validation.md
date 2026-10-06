# ✅ Phase 5 validation

**Rusjango 0.1.6 · Alpha**

Date: 2026-10-06. Phase 5 admin foundations are published as 0.1.6 from verified source commit `2a0ae27`.

## 🧪 Local checks

- Full suite: 155 tests passed on Python 3.11.16 and Python 3.14.7, with both CLIs and disposable live PostgreSQL.
- Four Rust workspace tests, formatting, and clippy passed.
- Python formatting and undefined/unused-code lint passed.
- Source archive and native wheel builds passed; the wheel was built from the source archive.
- Fresh wheel installations on Python 3.11 and 3.14 verified native version, admin factory/discovery, permission denial, catalog/read projection, typed writes, migration, CRUD, validation, generated pytest execution, and scaffold removal.
- The generated Docker image passed nonroot runtime, production host/error behavior, explicit migration, CRUD, admin discovery with no HTTP admin route, restart, and persisted SQLite data.

## 🔒 Admin regression coverage

Tests cover trusted-identity requirements, exact grants, denial before queries, independent registries, explicit visible fields, Boolean conversion, pagination, stable sorting, typed whitelisted filters, escaped literal search, and read-only defaults.

Write tests cover separate operation grants, required view access for returned data, schema validation, unknown/primary-key field rejection, hidden defaults, affected-row handling, and live PostgreSQL parameter numbering.

Discovery tests cover repeat loading, missing modules versus missing dependencies, rollback, and rejection of async factories/registration. Both CLIs use the same packaged admin template and preserve edited files and unrelated settings.

## 🔁 Reproduce

```bash
uv sync --all-packages --all-extras
cargo build -p rusjango-cli
RUSJANGO_RUST_CLI="$(pwd)/target/debug/rusjango" \
  .venv-postgres/bin/python scripts/test_postgres.py .venv/bin/python
python scripts/check_release.py v0.1.6
uv build --package rusjango
.venv/bin/python scripts/verify_wheel.py dist/rusjango-0.1.6-cp311-abi3-linux_x86_64.whl
.venv/bin/python scripts/verify_docker.py dist/rusjango-0.1.6-cp311-abi3-linux_x86_64.whl
```

See [contributing](10-contributing.md) for the disposable PostgreSQL helper and Python/Rust checks. Choose the wheel matching your platform.

## 🌍 Hosted gates

- [Main CI](https://github.com/babar-xagi/Rusjango/actions/runs/37476036253): all 13 jobs passed, including Python 3.11–3.14 on Windows/macOS/Linux and Rust/PostgreSQL/distribution/Docker integration.
- [Release workflow](https://github.com/babar-xagi/Rusjango/actions/runs/37476482332): all 22 jobs passed, including repeated validation, five platform wheels, source archive, strict metadata checks, PyPI upload, and GitHub release creation.
- [PyPI 0.1.6](https://pypi.org/project/rusjango/0.1.6/) contains five wheels and one source archive. The [GitHub release](https://github.com/babar-xagi/Rusjango/releases/tag/v0.1.6) contains all six artifacts and release notes.
- A published Linux wheel downloaded from PyPI matched its recorded SHA-256. Its fresh Python 3.14 installation passed native imports/version, all three feature scaffolds, admin permissions/read/write checks, migration, CRUD/validation, generated pytest execution, and feature removal.

## 🧭 Boundaries

The tests verify a trusted server-side service. They do not establish authentication, a browser dashboard, object-level authorization, transaction semantics, or production readiness. No HTTP admin routes are installed.

---

[📚 Documentation home](README.md) · [Admin tutorial](17-admin.md) · [Release notes](releases/0.1.6.md)
