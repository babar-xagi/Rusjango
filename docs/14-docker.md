# 🐳 Run with Docker

**Rusjango 0.1.5 · Alpha**

The Docker scaffold supplies a multi-stage image, Compose configuration, an ASGI entry point, and production-oriented settings. This guide continues with the school ORM app from the [ORM tutorial](05-orm-guide.md).

## 📁 Add the scaffold

Stop the development server, then:

```bash
uv run rusjango add docker
```

Generated files:

| File | Purpose |
|---|---|
| `Dockerfile` | Build dependencies separately and run as UID 10001 |
| `compose.yml` | Web service and a named volume at `/data` |
| `.dockerignore` | Exclude the venv, Git metadata, caches, .env files, and common database files |
| `settings_docker.py` | Load the configured base settings, disable DEBUG, and apply environment overrides |
| `docker_app.py` | Import the configured Rusjango object and apply container settings |
| `.rusjango-features.json` | Track original generated content for safe removal |

Existing files and alternate Compose filenames are preserved: a conflict stops scaffolding before files are created. Repeated adds do not rewrite a tracked scaffold.

## 🔒 Configure allowed hosts

Compose requires an explicit allowlist:

```bash
export ALLOWED_HOSTS=localhost,127.0.0.1
```

For a public hostname, use its actual domain instead. In PowerShell, set `$env:ALLOWED_HOSTS = "localhost,127.0.0.1"`.

The generated settings force `DEBUG = False` and include SecurityMiddleware. Missing allowed hosts stop startup. Invalid/disallowed Host headers receive 400.

## 🛠️ Build the image

```bash
docker compose build
```

The builder uses uv to install production dependencies without dev extras. The runtime starts Uvicorn on port 8000 without development reload.

Commit `uv.lock` when you want dependency versions recorded. Local dependencies used by the build must be inside the Docker build context.

## 🗃️ Create tables explicitly

When ORM is configured:

```bash
docker compose run --rm web /app/.venv/bin/python -m rusjango migrate
```

The image sets `RUSJANGO_SETTINGS=settings_docker.py`, so migrations and the server use the same container database configuration.

Skip this step for an application with `DATABASE = None`. Startup never creates tables automatically.

## ▶️ Start and check

```bash
docker compose up -d
docker compose logs -f web
```

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/school/students
```

The SQLite file lives at `/data/db.sqlite3` in the named volume. It survives service restart.

Stop the service with `docker compose down`. Adding `--volumes` also removes the named volume and its database data; use that only when you intend to delete it.

## 🐘 PostgreSQL

Install `rusjango[postgres]` in the project before building. With ORM enabled, set:

```bash
export DATABASE_URL=postgresql://user:password@database:5432/demo
```

The configured database switches to PostgreSQL. Compose does not scaffold a PostgreSQL service; supply a reachable database yourself. Rebuild after changing dependencies and run migrations explicitly.

For SQLite, `DATABASE_NAME` controls its path; Compose supplies `/data/db.sqlite3`.

## 🧹 Remove scaffolding

```bash
uv run rusjango remove docker
```

Removal asks for confirmation. Unchanged tracked files are removed; edited files are preserved and reported. `--yes` skips the prompt but still preserves modifications.

Keep the ownership manifest under version control with the scaffold. Removal does not stop running containers, remove images, delete volumes, or change base settings.

## 🧭 Deployment scope

This is a configuration example, not a production-readiness claim. Auth, TLS termination, tracked migrations, and request limits remain separate work. Use the [validation record](16-phase4-validation.md) to see the tested container behavior.

---

[← Middleware](07-middleware.md) · [📚 Documentation home](README.md) · [Next: Application tests →](15-testing.md)
