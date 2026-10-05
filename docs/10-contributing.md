# Contributing and validation

Applies to Rusjango 0.1.4 (alpha).

Work from a clean source checkout with Python 3.11+, stable Rust, and uv. Use one OS environment consistently; on WSL2 the repository is `/mnt/d/Rusjango`.

```bash
uv sync --all-packages --all-extras
cargo build -p rusjango-cli
RUSJANGO_RUST_CLI="$(pwd)/target/debug/rusjango" \
  uv run --all-packages --all-extras pytest python/rusjango/tests -q
cargo fmt --all -- --check
PYO3_PYTHON="$(pwd)/.venv/bin/python" cargo test --workspace
PYO3_PYTHON="$(pwd)/.venv/bin/python" cargo clippy --workspace --all-targets -- -D warnings
uv run ruff check python/rusjango/src python/rusjango/tests scripts --select F
uv build --package rusjango
```

On Windows the Rust binary has an .exe suffix and the virtual environment interpreter is `.venv/Scripts/python.exe`. CI tests Python 3.11â€“3.14 and checks the installed extension and both CLIs.

## Real PostgreSQL tests

Point RUSJANGO_TEST_POSTGRES_DSN at a disposable database and rerun pytest. The tests create uniquely named tables and remove them afterward. Without that environment variable, the two live backend tests skip explicitly; SQL and pool-release regressions still run.

For a local disposable server without a system PostgreSQL service, the optional runner uses a separate Python 3.12 environment because pgserver publishes wheels for that version:

```bash
uv venv --python 3.12 .venv-postgres
uv pip install --python .venv-postgres/bin/python pgserver==0.1.4
RUSJANGO_RUST_CLI="$(pwd)/target/debug/rusjango" \
  .venv-postgres/bin/python scripts/test_postgres.py .venv/bin/python
```

The runner starts an isolated temporary server, passes its DSN to the suite, and stops it afterward. pgserver is a test aid, not a runtime dependency.

## Contribution rules

Keep the initial scaffold to three files. Preserve custom code when adding features. Destructive commands need confirmation. Test regression triggers and failure paths, not just happy paths. Keep Python and Rust command behavior aligned and versions consistent. Update relevant docs and the phase tracker with implemented scope and remaining limits.

Never claim Rust performance, production safety, or feature completeness without evidence. Changes to model table names require explicit data-migration guidance. Do not publish packages or run feature-destructive commands as part of routine tests against a real user project.

For an explicitly authorized publication, follow the [release procedure](12-releasing.md). [0.1.4 release notes](releases/0.1.4.md) describe this repair pass and its compatibility changes.
