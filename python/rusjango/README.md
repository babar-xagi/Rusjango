# Rusjango 0.1.4

An alpha async Python API framework with Django-style apps, progressive scaffolding, and a separate Rust CLI. The native extension is a placeholder and currently does not accelerate requests.

Requires Python 3.11+. Install into a virtual environment:

```bash
pip install rusjango==0.1.4
# Optional PostgreSQL driver:
pip install 'rusjango[postgres]==0.1.4'
```

```bash
rusjango new demo
cd demo
uv sync
rusjango add app school
rusjango add orm
rusjango migrate
rusjango dev
```

Implemented: async JSON routes, typed primitive parameters, strict schemas, middleware, app mounting, SQLite/PostgreSQL CRUD, and table creation. Scaffolding preserves custom APIs and unrelated settings.

The ORM has no tracked migrations, transaction API, or relationships. Auth, admin, OpenAPI, workers, and Rust request acceleration remain pending. SQLite requires 3.35+; old databases affected by the `model` table-name bug need explicit data migration.

Read the [project README](../../README.md), [full documentation](../../docs/00-overview.md), [release notes](../../docs/releases/0.1.4.md), and [validation record](../../docs/11-validation.md). Package metadata uses the root README as the canonical PyPI description.
