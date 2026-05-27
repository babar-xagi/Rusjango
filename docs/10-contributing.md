# Contributing

Thank you for contributing to Rusjango. This document covers how to set up a development environment, run tests, and follow the project's conventions.

---

## Dev environment setup

**Prerequisites:**
- Rust (stable toolchain) — install via [rustup](https://rustup.rs/)
- Python 3.11+ — managed by [uv](https://docs.astral.sh/uv/)
- `uv` — install via `pip install uv` or the official installer
- `maturin` — installed automatically through `uv sync`

**Clone and build:**

```bash
git clone <repo>
cd rusjango

# Install Python dependencies (creates .venv, installs dev tools)
uv sync

# Build and install the Rust extension (rusjango._core) into the venv
uv run maturin develop -m python/rusjango/pyproject.toml

# Build the CLI binary
cargo build -p rusjango-cli
```

After this, `rusjango` is available at `target/debug/rusjango` and the Python package is importable from the project's virtual environment.

**Quick check:**

```bash
uv run python -c "import rusjango; print(rusjango.__version__)"
./target/debug/rusjango --help
```

---

## Running tests

```bash
cd python/rusjango
uv run pytest tests/ -v
```

Run a single test file:

```bash
uv run pytest tests/test_routing.py -v
```

Run with coverage:

```bash
uv run pytest tests/ --cov=rusjango --cov-report=term-missing
```

All tests must pass before a pull request is merged.

---

## Project structure rules

| Path | Contents |
|---|---|
| `python/rusjango/src/rusjango/` | All Python source code for the framework |
| `cli/src/` | All Rust source code for the CLI |
| `crates/` | Shared Rust crates (e.g., `rusjango-core` PyO3 extension) |
| `templates/` | Project and app scaffold templates (`.tpl` files) |
| `docs/` | All documentation |
| `python/rusjango/tests/` | Python test suite |

**Rules:**
- Never add binary files (`.pyd`, `.so`, `.pdb`, `.dll`) to git — they are build artifacts and are covered by `.gitignore`.
- Document every new feature in `docs/` before or alongside the implementation.
- Do not add runtime dependencies to the core framework without discussion — keep the default install lightweight.

---

## Adding a new CLI command

1. **Create a new source file** in `cli/src/` (e.g., `cli/src/admin.rs`).

2. **Define the command logic** — follow the pattern in existing command files (`add.rs`, `remove.rs`):
   ```rust
   use anyhow::Result;

   pub fn run_admin(/* args */) -> Result<()> {
       // implementation
       Ok(())
   }
   ```

3. **Register the subcommand** in `cli/src/main.rs`:
   - Add a variant to the `Commands` enum with `#[command(...)]` attributes.
   - Add a match arm in `main()` that calls your new function.

4. **Add any new templates** to `templates/<feature>/` as `.tpl` files using `{{ variable }}` substitution syntax.

5. **Write tests** in `python/rusjango/tests/` covering the CLI behaviour (scaffolding output, settings changes, etc.).

6. **Update documentation:**
   - `docs/03-cli-reference.md` — add the new command to the reference table.
   - `docs/09-progress.md` — update the relevant phase status.

---

## Adding a new Python module

1. **Create the file** in `python/rusjango/src/rusjango/` (e.g., `auth.py`).

2. **Export the public API** from `__init__.py`:
   ```python
   from rusjango.auth import require_auth, User
   ```

3. **Write tests** in `python/rusjango/tests/test_<module>.py`:
   ```python
   from __future__ import annotations
   import pytest
   from rusjango.auth import User

   @pytest.mark.asyncio
   async def test_user_creation():
       ...
   ```

4. **Document the module** in the appropriate `docs/` file, or create a new one if the feature warrants it.

---

## Code style

### Python

- Add `from __future__ import annotations` at the top of every new file.
- Follow the existing code patterns — match imports style, naming conventions, and docstring format.
- Keep functions short and focused; avoid classes where a function suffices.
- All new tests must be async-compatible — use `@pytest.mark.asyncio` or configure `asyncio_mode = "auto"` in `pyproject.toml`.
- No external formatters are enforced yet, but aim for PEP 8 compliance.

### Rust

- Run `cargo fmt` before committing any Rust changes:
  ```bash
  cargo fmt --all
  ```
- Run `cargo clippy` and fix all warnings before committing:
  ```bash
  cargo clippy --all-targets --all-features -- -D warnings
  ```
- Use `anyhow::Result` for error propagation in CLI code.
- Prefer `thiserror` for library error types in `rusjango-core`.

---

## Development philosophy

These rules come from the project design document and must be respected in all contributions:

1. **Keep the default project tiny** — a new `rusjango new` project must contain only the files that are always needed. Nothing extra.
2. **Never generate unnecessary files by default** — opt-in scaffolding only.
3. **Every feature should be removable** — `rusjango add X` must have a corresponding `rusjango remove X`.
4. **Every command should update settings automatically** — the CLI is the source of truth for `settings.py` changes; the developer should not need to edit it manually for standard operations.
5. **Dangerous commands must ask for confirmation** — any destructive action (deleting files, dropping tables) must prompt the user with `y/N` before proceeding.
6. **ORM must be async-first** — all database operations use `aiosqlite` or `asyncpg`; no synchronous DB calls.
7. **Python libraries must work normally** — Rusjango must not prevent or interfere with using third-party Python packages (FastAPI patterns, Pydantic, SQLAlchemy, etc.).
8. **Rust should speed up internals, not replace Python** — Rust is used for the CLI and hot paths; the developer-facing API stays in Python.
9. **Documentation must be written from day one** — no feature is considered complete until it is documented in `docs/`.

---

## Pull request checklist

Before opening a PR:

- [ ] All existing tests pass (`uv run pytest tests/ -v`).
- [ ] New functionality has tests.
- [ ] `cargo fmt --all` and `cargo clippy` pass with no warnings.
- [ ] Relevant `docs/` files are updated.
- [ ] `docs/09-progress.md` phase status is updated if applicable.
- [ ] No binary build artifacts are staged for commit.
