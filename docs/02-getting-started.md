# Getting started

Applies to Rusjango 0.1.4 (alpha).

Requires Python 3.11+, stable Rust, and uv for source development.

## WSL2 setup

Run these in the WSL shell:

```bash
cd /mnt/d/Rusjango
uv sync --all-packages --all-extras
cargo build -p rusjango-cli
cd examples/hello
uv run python -m rusjango migrate
uv run python -m rusjango dev
```

The virtual environment is Linux-specific; do not reuse it from Windows Python. `uv sync` builds the extension with maturin. If Rust linking picks an incomplete system Python, set PYO3_PYTHON to the absolute `.venv/bin/python` path when running Cargo checks.

The repository's `.python-version` pins Python 3.12. To use your installed Python 3.14, run `uv sync --python 3.14 --all-packages --all-extras` and pass `--python 3.14` to subsequent `uv run` commands, or set `UV_PYTHON=3.14` in that shell. Python 3.11 is the minimum supported version.

## Generated project using this checkout

From the repository root:

```bash
uv run python -m rusjango new demo
uv venv demo/.venv
uv pip install --python demo/.venv/bin/python -e ./python/rusjango
cd demo
.venv/bin/python -m rusjango add app school
.venv/bin/python -m rusjango add orm
.venv/bin/python -m rusjango migrate
.venv/bin/python -m rusjango dev
```

Installing from the checkout exercises unreleased changes. Otherwise, a generated project's `uv sync` resolves `rusjango` from the package index.

## Test the example

```bash
curl http://127.0.0.1:8000/api/school/students
curl -X POST http://127.0.0.1:8000/api/school/students \
  -H 'Content-Type: application/json' -d '{"name":"Ali","age":20}'
```

`age` may be omitted or null. An invalid type returns 422. Shut down with Ctrl+C. Table creation does not happen automatically during startup.
