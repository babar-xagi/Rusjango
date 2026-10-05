# Rust internals

Applies to Rusjango 0.1.4 (alpha).

The workspace has two crates: rusjango-cli and rusjango-core. Versions are inherited from the workspace, currently 0.1.4.

## Core extension

PyO3 builds rusjango._core. It exports a version string and placeholder route_count returning zero. It is not connected to the Python route table and performs no request acceleration.

The build uses PyO3's stable ABI for Python 3.11+. Maturin configures extension linking; Cargo test builds use the interpreter selected by PYO3_PYTHON. Point it to an absolute environment interpreter path if the system Python lacks its development library.

## CLI

Clap handles commands. Scaffolding templates are included with include_str at compile time. Installed binaries no longer read files from CARGO_MANIFEST_DIR at runtime.

Project detection parses TOML. Literal app lists and DATABASE assignments are edited within their value ranges, preserving unrelated settings. This is intentionally not a general Python parser. Unsupported computed values are rejected; edited-value comments may be lost.

The dev/migrate commands spawn Python through uv when available. Missing uv triggers a direct Python fallback; failed migration subprocesses produce a nonzero CLI exit.
