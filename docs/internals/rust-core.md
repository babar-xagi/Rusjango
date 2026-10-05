# 🦀 Rust internals

**Rusjango 0.1.4 · Alpha**

The workspace contains `rusjango-cli` and `rusjango-core`. Both inherit version **0.1.4** from the workspace.

## 📦 Native extension

PyO3 builds `rusjango._core`. The extension exports:

| Export | Behavior |
|---|---|
| `__version__` | Native package version |
| `route_count` | Placeholder returning zero |

The placeholder is not connected to the Python route table. Requests are not accelerated by Rust today.

The build targets the stable ABI for Python 3.11+. Maturin configures extension linking. Cargo tests use the interpreter selected through `PYO3_PYTHON`.

```bash
PYO3_PYTHON="$(pwd)/.venv/bin/python" cargo test --workspace
```

Use an absolute interpreter path when system Python lacks its development library.

## 🛠️ Standalone CLI

Clap handles command parsing. Templates are embedded with `include_str!` at compile time, so the installed binary does not read source-checkout templates.

Project detection parses TOML. Literal app lists and DATABASE assignments are edited within value ranges while preserving unrelated settings.

The Rust editor is intentionally a limited literal-settings editor. Unsupported computed values are rejected; comments inside edited values may be lost.

## ▶️ Python subprocesses

Dev/migrate prefer uv. If uv is missing, they fall back to direct Python.

Migration process failures produce nonzero CLI exits. Existing PYTHONPATH entries are preserved when source lookup adds a path.

## 🔎 Source

- [Core module](../../crates/rusjango-core/src/lib.rs)
- [Rust CLI](../../cli/src/main.rs)
- [Project/template helpers](../../cli/src/project.rs)
- [Settings editor](../../cli/src/settings.rs)

---

[📚 Documentation home](../README.md) · [Architecture](../01-architecture.md) · [Contributing →](../10-contributing.md)
