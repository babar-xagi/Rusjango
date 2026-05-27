# Rusjango

Rust-powered async Python web framework. Start minimal, grow with `rusjango add`.

## Monorepo layout

```
rusjango/
├── Cargo.toml              # Rust workspace (core + CLI)
├── pyproject.toml          # uv workspace root
├── crates/rusjango-core/   # PyO3 extension (routing, HTTP)
├── cli/                    # `rusjango` binary (clap)
├── python/rusjango/        # Python package (maturin)
├── templates/              # `new` / `add app` scaffolds
└── examples/               # Dogfood projects
```

## Prerequisites

- [Rust](https://rustup.rs/)
- [uv](https://docs.astral.sh/uv/)

## Development setup

```bash
cd rusjango

# Python workspace + dev tools
uv sync

# Build and install the extension into the venv
uv run maturin develop -m python/rusjango/pyproject.toml

# Rust CLI
cargo build -p rusjango-cli
cargo run -p rusjango-cli -- --help
```

## Quick start

```bash
# Build CLI and Python package
cargo build -p rusjango-cli
cd python/rusjango && uv run maturin develop && cd ../..

# Run the example project (must be inside examples/hello)
cd examples/hello
uv sync
uv run python -m rusjango._dev

# Or from examples/:  .\dev.ps1
# Or:  uv run --project examples/hello python -m rusjango._dev
# Or from repo root after `cargo install --path cli`:
# cd examples/hello && rusjango dev
```

## Commands

| Command | Description |
|---------|-------------|
| `rusjango new <name>` | Create `main.py`, `settings.py`, `pyproject.toml` |
| `rusjango dev` | Start dev server (uvicorn + auto-reload) |
| `rusjango add app <name>` | Create `apps/<name>/` and register in `INSTALLED_APPS` |
| `rusjango remove app <name>` | Remove app directory (prompts for confirmation) |
| `rusjango add orm` | Enable SQLite ORM, add `models.py` / `schemas.py` to apps |
| `rusjango remove orm` | Set `DATABASE = None` (keeps model files) |
| `rusjango migrate` | Create database tables from models |

## Status

Phase 3 ORM: async SQLite, Model CRUD, filters (`__gte`, `__lte`, …), Schema helpers, migrate. App routes under `/api/<app>/`.
