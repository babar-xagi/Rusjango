# Examples

Run the sample app from **`hello/`**, not from this `examples/` folder.

```powershell
cd hello
uv sync
uv run python -m rusjango._dev
```

Or from anywhere in the repo:

```powershell
uv run --project examples/hello python -m rusjango._dev
```

From the monorepo root (after `uv sync` and `maturin develop`):

```powershell
uv sync
cd python/rusjango
uv run maturin develop
cd ../../examples/hello
uv run python -m rusjango._dev
```

If you see `No module named 'rusjango'`, you ran `uv sync` in the wrong directory and dropped the package from the venv. Use `cd hello` and `uv sync` again.
