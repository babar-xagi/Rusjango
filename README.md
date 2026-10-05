# Rusjango

An experimental async Python API framework with Django-style apps and an optional Rust extension.

**Version: 0.1.4. Status: alpha.** Phases 1-3 provide routing, app scaffolding, and a basic async ORM. The Rust CLI is implemented; the Rust runtime core is a placeholder and currently provides no routing or serialization acceleration. Auth, admin, OpenAPI, workers, AI helpers, and enterprise features are not implemented.

## What works

- A three-file project: `main.py`, `settings.py`, `pyproject.toml`.
- Async GET, POST, PUT, and DELETE handlers with JSON responses.
- Literal paths and typed path/query parameters; invalid input returns 422.
- Strict schemas with required fields, defaults, optional types, nested schemas, lists, and dictionaries.
- ASGI middleware, production host validation, and security response headers.
- Independent application routers under `/api/<app>/`.
- SQLite and PostgreSQL CRUD with parameterized values, generated integer IDs, and affected-row counts.
- Table creation through `migrate`; existing schema changes require manual SQL.
- Python CLI included in the package and a separate Rust CLI with embedded templates.

## Develop from source

Requires Python 3.11+, Rust, and [uv](https://docs.astral.sh/uv/). On Windows, use the Linux environment for all commands below when working in WSL2.

```bash
cd /mnt/d/Rusjango  # WSL2 path for D:\Rusjango
uv sync --all-packages --all-extras
cargo build -p rusjango-cli

cd examples/hello
uv run python -m rusjango migrate
uv run python -m rusjango dev
```

Visit `http://127.0.0.1:8000/` or `/api/school/students`. Migration is an explicit command; server startup never creates or alters tables.

For a published package, install `rusjango` into a virtual environment, then use:

```bash
rusjango new demo
cd demo
uv sync
rusjango add app school
rusjango add orm
rusjango migrate
rusjango dev
```

A generated project depends on the published package. To exercise unreleased source changes, use the repository example or install this checkout into the generated project's environment. See [getting started](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/02-getting-started.md).

## Example API

```python
from rusjango import Rusjango, Schema

app = Rusjango()

class Greeting(Schema):
    name: str
    age: int | None = None

@app.post('/hello')
async def hello(data: Greeting):
    return {'message': f'Hello {data.name}', 'age': data.age}
```

JSON schema fields use strict types: `"20"` is not an integer. Extra object keys are ignored. Path and query strings support `str`, `int`, `float`, and `bool` conversion.

## Safe scaffolding

`add orm` upgrades an API only when it still matches the untouched starter template. Custom routes, models, and schemas are preserved. Apps added after ORM activation receive ORM scaffolding too. Removal asks for confirmation unless `--yes` is supplied.

The CLI edits literal settings assignments. It preserves unrelated settings, but may normalize the edited list/dictionary and remove comments inside that value. Computed settings should be edited manually. `remove orm` preserves application code; routes that use the ORM need to be removed or adapted by the developer.

## Test and build

```bash
uv run --all-packages --all-extras pytest python/rusjango/tests -q
cargo fmt --all -- --check
PYO3_PYTHON="$(pwd)/.venv/bin/python" cargo test --workspace
PYO3_PYTHON="$(pwd)/.venv/bin/python" cargo clippy --workspace --all-targets -- -D warnings
uv run ruff check python/rusjango/src python/rusjango/tests scripts --select F
uv build --package rusjango
```

To exercise the Rust CLI alongside Python, build it first and set `RUSJANGO_RUST_CLI` to its absolute binary path. Real PostgreSQL tests require `RUSJANGO_TEST_POSTGRES_DSN` pointing to a disposable test database. [Testing details](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/10-contributing.md).

The Phase 1–3 repair pass passed 74 tests on Python 3.11 and 3.14, including both CLIs and live PostgreSQL. Rust checks and clean distribution builds also passed. See the [validation record](https://github.com/babar-xagi/Rusjango/blob/main/docs/11-validation.md) for scope and reproduction steps.

## Current limits

One database configuration per process; no multi-database isolation, relationships, transaction API, tracked migrations, auth, admin, OpenAPI generation, streaming, uploads, or supported WebSockets. SQLite requires version 3.35+ for `INSERT ... RETURNING`. Request bodies are buffered in memory. There are no performance benchmarks proving an advantage over other frameworks.

Existing databases created by the old default-table bug may contain a table named `model`. The fix does not rename that table or move its data. Back up those databases and migrate data explicitly before adopting corrected model table names.

## Documentation

Start with the [overview](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/00-overview.md), [architecture](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/01-architecture.md), [CLI reference](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/03-cli-reference.md), [API guide](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/04-api-design.md), and [ORM guide](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/05-orm-guide.md). [PROGRESS.md](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/PROGRESS.md) tracks the phase gates.

Additional guides: [settings](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/06-settings-reference.md), [middleware](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/07-middleware.md), [schemas](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/08-schema-validation.md), [contributing](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/10-contributing.md), [validation](https://github.com/babar-xagi/Rusjango/blob/main/docs/11-validation.md), and [release procedure](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/12-releasing.md). [Release notes](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/docs/releases/0.1.4.md) explain compatibility changes.

MIT licensed. See [LICENSE](https://github.com/babar-xagi/Rusjango/blob/v0.1.4/LICENSE).
