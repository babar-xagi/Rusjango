# 🦀 Rusjango

**Async Python APIs with Django-style apps and progressive scaffolding.**

[![PyPI](https://img.shields.io/pypi/v/rusjango)](https://pypi.org/project/rusjango/)
[![Python](https://img.shields.io/pypi/pyversions/rusjango)](https://pypi.org/project/rusjango/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](../../LICENSE)

## 🚀 Start a project

Requires Python 3.11+ and uv:

```bash
uvx --from rusjango==0.1.5 rusjango new demo
cd demo
uv sync
uv run rusjango dev
```

Open **http://127.0.0.1:8000/**.

## ✨ Implemented

Async JSON routes, typed path/query parameters, schemas with opt-in coercion/constraints/validators, independent app routers, ASGI middleware, SQLite/PostgreSQL CRUD, and a complete Python CLI. Both CLIs scaffold Docker and isolated ASGI tests while preserving edited files.

> 🧪 **0.1.5 is alpha.** The native extension remains a placeholder. Auth, admin, OpenAPI, relationships, transactions, and tracked migrations are pending.

## 📚 Learn more

- [Project README and examples](../../README.md)
- [Documentation home](../../docs/README.md)
- [First steps](../../docs/02-getting-started.md)
- [Release notes](../../docs/releases/0.1.5.md)
- [Validation record](../../docs/16-phase4-validation.md)

The package metadata uses the root README as the canonical PyPI description.
