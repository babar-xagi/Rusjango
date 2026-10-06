# 🤝 Contributing

**Rusjango 0.1.6 · Alpha**

Contributions should improve implemented behavior, preserve existing application code, and keep the documentation accurate.

## 🧰 Set up source development

Use Python 3.11+, stable Rust, and uv. Run all commands in one OS environment.

In WSL2:

```bash
cd /mnt/d/Rusjango
uv sync --all-packages --all-extras
cargo build -p rusjango-cli
```

The repository pins Python 3.12. Set `UV_PYTHON=3.14` before uv commands when you want Python 3.14.

On Windows, the environment interpreter is `.venv/Scripts/python.exe` and the Rust CLI binary has an `.exe` suffix.

## 🧪 Run Python and CLI checks

From the repository root in Linux/WSL:

```bash
RUSJANGO_RUST_CLI="$(pwd)/target/debug/rusjango" \
  uv run --all-packages --all-extras pytest python/rusjango/tests -q
```

Set `RUSJANGO_TEST_POSTGRES_DSN` to include live PostgreSQL tests. Without a DSN, the PostgreSQL tests skip. Without a Rust CLI path, its integration cases skip.

> 💡 **Use a disposable database:** PostgreSQL tests create uniquely named tables and clean them up. Test against a database intended for tests.

## 🐘 Start a disposable PostgreSQL server

The optional runner can start a temporary server without a system PostgreSQL service:

```bash
uv venv --python 3.12 .venv-postgres
uv pip install --python .venv-postgres/bin/python pgserver==0.1.4

RUSJANGO_RUST_CLI="$(pwd)/target/debug/rusjango" \
  .venv-postgres/bin/python scripts/test_postgres.py .venv/bin/python
```

The helper environment uses Python 3.12 for the pgserver wheel. The test suite still runs with the interpreter passed as the final argument.

The runner stops the isolated server afterward. pgserver is a development aid, not a Rusjango runtime dependency.

## 🦀 Check Rust

```bash
cargo fmt --all -- --check
PYO3_PYTHON="$(pwd)/.venv/bin/python" cargo test --workspace
PYO3_PYTHON="$(pwd)/.venv/bin/python" cargo clippy --workspace --all-targets -- -D warnings
```

Use an absolute interpreter path when system Python lacks its development library.

## 🧹 Check Python style

```bash
uv run --all-packages --all-extras ruff format --check python/rusjango/src python/rusjango/tests scripts
uv run --all-packages --all-extras ruff check python/rusjango/src python/rusjango/tests scripts --select F
```

## 📦 Check packaging

```bash
python scripts/check_release.py
uv build --package rusjango
.venv/bin/python scripts/verify_wheel.py dist/rusjango-0.1.6-cp311-abi3-linux_x86_64.whl
```

Select the wheel for the version and platform you built. The helper installs it into a fresh environment and checks the native module, scaffolds, migration, API, admin permissions/data services, generated tests, and feature removal.

## ✍️ Keep contributions focused

- Preserve the three-file initial scaffold.
- Preserve custom code when adding a feature.
- Keep Python/Rust commands and package versions consistent.
- Test meaningful regression triggers and failure paths.
- Run checks appropriate to the change.
- Update the relevant tutorial, reference, and phase tracker.
- Provide data-migration guidance when changing model table behavior.

Do not claim production safety, Rust performance, or feature completeness without evidence.

Routine validation does not publish a package. An explicitly authorized release follows the [release procedure](12-releasing.md).

---

[📚 Documentation home](README.md) · [Validation record →](11-validation.md)
