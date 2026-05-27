# Rust Core Internals

Rusjango uses two Rust crates: a PyO3 extension (`rusjango-core`) that is compiled into the Python package, and a standalone CLI binary (`rusjango-cli`). This document explains how each is structured and why those tools were chosen.

---

## Crate: `rusjango-core`

**Location:** `crates/rusjango-core/`

`rusjango-core` is a native Python extension module built with [maturin](https://github.com/PyO3/maturin) and [PyO3](https://pyo3.rs/). It compiles to:

- `rusjango/_core.pyd` on Windows
- `rusjango/_core.so` on Linux / macOS

The compiled artifact is imported by `rusjango/__init__.py` as:

```python
from rusjango import _core
```

### Current surface area

| Symbol | Type | Description |
|---|---|---|
| `__version__` | `str` | Matches the `version` field in `Cargo.toml` |
| `route_count()` | `fn() -> int` | Returns the number of registered routes (placeholder for future routing acceleration) |

These are intentionally minimal — the extension exists primarily as the foundation for future performance-critical work.

### Planned extensions

| Feature | Status |
|---|---|
| Routing acceleration (regex matching in Rust) | Planned |
| JSON serialization via `serde_json` | Planned |
| Connection pooling hooks | Planned |
| Cryptographic utilities (HMAC, argon2) | Planned (Phase 6) |

### Building the extension

During development:

```bash
uv run maturin develop -m python/rusjango/pyproject.toml
```

For a release wheel:

```bash
uv run maturin build --release -m python/rusjango/pyproject.toml
```

The resulting `.whl` file in `target/wheels/` contains the compiled `.pyd` / `.so` and is installed with `pip install`.

---

## Crate: `rusjango-cli`

**Location:** `cli/`

`rusjango-cli` is the standalone binary that developers interact with (`rusjango new`, `rusjango dev`, `rusjango add app`, etc.). It is **not** a Python extension — it is compiled to a native executable.

```bash
cargo build -p rusjango-cli          # debug
cargo build -p rusjango-cli --release # optimised
```

Output: `target/debug/rusjango` (or `target/release/rusjango`)

### Architecture

```
cli/src/
  main.rs       ← clap Commands enum; dispatches to subcommand modules
  new.rs        ← rusjango new <name>
  dev.rs        ← rusjango dev
  add.rs        ← rusjango add <feature>
  remove.rs     ← rusjango remove <feature>
  orm.rs        ← rusjango migrate + add/remove orm
  settings.rs   ← settings.py read/patch utilities
```

### Python delegation

The CLI does not run Python code directly inside the Rust process. Instead, it spawns subprocesses via `uv`:

```rust
// dev.rs (simplified)
std::process::Command::new("uv")
    .args(["run", "uvicorn", "asgi:app", "--reload"])
    .spawn()?;
```

For operations that need Python at runtime (e.g., running `migrate`), the CLI invokes:

```bash
uv run python -m rusjango._dev <args>
```

This keeps the Rust binary small and avoids embedding a Python interpreter.

### Template rendering

New project and app scaffolding reads `.tpl` files from the `templates/` directory and performs simple variable substitution using the `regex` crate:

```rust
// Substitution targets in .tpl files:
//   {{ project_name }}  → replaced with the new project's name
//   {{ secret_key }}    → replaced with a randomly generated hex string

let content = template_str
    .replace("{{ project_name }}", &project_name)
    .replace("{{ secret_key }}", &generated_key);
```

For the secret key, the CLI generates 32 cryptographically random bytes using the `rand` crate:

```rust
use rand::Rng;
let key: String = rand::thread_rng()
    .sample_iter(&rand::distributions::Alphanumeric)
    .take(64)
    .map(char::from)
    .collect();
```

### Settings manipulation

The `settings.rs` module reads and patches `settings.py` using regex-based search-and-replace. This avoids a Python runtime dependency for settings changes during `add`/`remove` operations:

```rust
// Adding an app to INSTALLED_APPS (simplified)
let re = Regex::new(r"INSTALLED_APPS\s*=\s*\[([^\]]*)\]")?;
let new_content = re.replace(&content, |caps: &Captures| {
    format!("INSTALLED_APPS = [{}    \"{}\",\n]", &caps[1], app_name)
});
```

---

## PyO3 basics

PyO3 bridges Rust functions and types into Python. The module entry point follows this pattern:

```rust
use pyo3::prelude::*;

/// Exposed to Python as rusjango._core
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_function(wrap_pyfunction!(route_count, m)?)?;
    Ok(())
}

#[pyfunction]
fn route_count() -> PyResult<usize> {
    // Placeholder — will query the global route registry
    Ok(0)
}
```

The `#[pymodule]` attribute generates the C extension initializer (`PyInit__core`). Maturin handles linking, wheel metadata, and platform naming automatically.

---

## Why these Rust tools

| Crate | Role | Rationale |
|---|---|---|
| `pyo3` | Rust ↔ Python bindings | The standard, actively maintained crate for native Python extensions in Rust. Used by Polars, Ruff, and others. |
| `maturin` | Build and publish PyO3 extensions | Handles cross-compilation, wheel packaging, and `pip install` integration without manual `setup.py`. |
| `clap` | CLI argument parsing | Fastest and most ergonomic CLI framework in the Rust ecosystem; generates `--help` text automatically from struct/enum attributes. |
| `tokio` | Async runtime | The de-facto standard async runtime for Rust; used internally for any async I/O within the CLI (e.g., HTTP health checks). |
| `regex` | Regex engine | PCRE-like syntax, compiled once and reused; used for template substitution and `settings.py` patching. |
| `anyhow` | Error handling | Ergonomic `?`-based error propagation with `.context("...")` for human-readable error chains in CLI output. |
| `rand` | Random number generation | CSPRNG for secret key generation during `rusjango new`. |

---

## Relationship between the two crates

```
Developer's terminal
  │
  ▼
rusjango-cli (binary)
  ├── scaffolds files from templates/
  ├── patches settings.py
  └── spawns: uv run python / uv run uvicorn
                │
                ▼
          Python process
            ├── imports rusjango (Python package)
            │     └── imports rusjango._core  ← rusjango-core (compiled .pyd/.so)
            └── runs the ASGI application
```

The Rust binary and the Python extension are independent artifacts. They do not share memory or communicate at runtime — the CLI is a developer tool, while the extension accelerates the running application.
