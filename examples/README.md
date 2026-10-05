# Example application

Applies to Rusjango 0.1.4 (alpha).

Run the bundled school API from `examples/hello`. From the repository root in WSL2:

```bash
uv sync --all-packages --all-extras
cd examples/hello
uv run python -m rusjango migrate
uv run python -m rusjango dev
```

Visit `http://127.0.0.1:8000/api/school/students`. Create a student with:

```bash
curl -X POST http://127.0.0.1:8000/api/school/students \
  -H 'Content-Type: application/json' -d '{"name":"Ali"}'
```

The optional age defaults to null. Invalid schema types return 422. Run `migrate` before requests that use the database; startup does not create tables.

The example uses the workspace package, so it exercises this checkout. Keep commands in one OS environment: WSL virtual environments cannot be reused by Windows Python. See [getting started](../docs/02-getting-started.md) for setup and generated-project instructions.
