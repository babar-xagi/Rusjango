# 📚 Rusjango documentation

**Learn by building a small API, then add applications and a database.**

These guides describe **Rusjango 0.1.5 (alpha)**. Each tutorial introduces one feature, shows code you can use, and explains the result.

> 💡 **New here?** Begin with [First steps](02-getting-started.md). You can install a published wheel without setting up Rust.

## 🚀 Tutorial

Follow this path in order, or jump to the feature you need.

| Step | Guide | You will learn |
|---|---|---|
| 1 | [First steps](02-getting-started.md) | Install, create a project, start the server, and check a response |
| 2 | [Routes and requests](04-api-design.md) | Path/query parameters, JSON bodies, status codes, and errors |
| 3 | [Schemas](08-schema-validation.md) | Required fields, defaults, optional types, nested objects, and lists |
| 4 | [Applications](13-applications.md) | Add apps and organize routes under independent prefixes |
| 5 | [Async ORM](05-orm-guide.md) | Define models and use SQLite/PostgreSQL CRUD |
| 6 | [Settings](06-settings-reference.md) | Configure the runtime and project entry point |
| 7 | [Middleware](07-middleware.md) | Wrap HTTP requests and configure basic security checks |
| 8 | [Docker](14-docker.md) | Build a nonroot image, configure hosts, and persist database data |
| 9 | [Application tests](15-testing.md) | Add an ASGI client fixture and isolated database tests |

## 🛠️ Reference

| Guide | Purpose |
|---|---|
| [Overview](00-overview.md) | Understand what Rusjango implements today |
| [CLI reference](03-cli-reference.md) | Look up commands, flags, and editing rules |
| [Architecture](01-architecture.md) | Follow the request flow and repository layout |
| [Progress](09-progress.md) | See phase boundaries and remaining work |
| [0.1.4 release notes](releases/0.1.4.md) | Review fixes and compatibility changes |

## 🤝 Contribute

| Guide | Purpose |
|---|---|
| [Contributing](10-contributing.md) | Set up source development and run appropriate checks |
| [Validation record](11-validation.md) | Review local tests and hosted release evidence |
| [Phase 4 validation](16-phase4-validation.md) | Review validation, feature-scaffold, package, and Docker checks |
| [Releasing](12-releasing.md) | Prepare, publish, and verify an authorized release |
| [Python internals](internals/python-layer.md) | Explore dispatch, settings, and app loading |
| [ORM internals](internals/orm-internals.md) | Understand model registration, SQL, and connection handling |
| [Rust internals](internals/rust-core.md) | Understand the CLI and placeholder PyO3 extension |

## 🧭 What is available?

**Implemented:** async JSON routes, primitive path/query conversion, strict schemas with opt-in coercion/validators/constraints, app mounting, ASGI middleware, basic host checks, SQLite/PostgreSQL CRUD, and app/ORM/Docker/test CLI scaffolding.

**Pending:** auth, admin, OpenAPI generation, transaction APIs, relationships, tracked migrations, workers, and Rust request acceleration.

The docs explain implemented behavior. Planned work lives in [PROGRESS.md](../PROGRESS.md).

---

[🏠 Project README](../README.md) · [🚀 Start the tutorial](02-getting-started.md)
