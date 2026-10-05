# 🛠️ CLI reference

**Rusjango 0.1.4 · Alpha**

Inside a uv-managed project, use `uv run rusjango`. In an activated pip environment, use `python -m rusjango`. A standalone Rust binary exposes the same commands.

## 🔎 Find help

```bash
uv run rusjango --help
uv run rusjango dev --help
uv run rusjango add app --help
```

## 📋 Commands

| Command | Behavior |
|---|---|
| `new <name> [-d DIR]` | Create `DIR/<name>` with three scaffold files |
| `dev [--host HOST] [--port PORT] [--no-reload]` | Start Uvicorn; reload is on by default |
| `add app <name>` | Scaffold, register, and mount an app |
| `remove app <name> [--yes]` | Confirm, unregister, and delete the app package |
| `add orm` | Configure SQLite if disabled and add ORM starter files |
| `remove orm [--yes]` | Set DATABASE to None and keep application files |
| `migrate` | Create missing model tables; return nonzero on failure |

### 🚀 New project

```bash
uvx --from rusjango==0.1.4 rusjango new demo
```

The destination must not already exist. Project names accept letters, digits, hyphens, and underscores.

### ▶️ Development server

```bash
uv run rusjango dev --host 127.0.0.1 --port 8080 --no-reload
```

The default host/port are `127.0.0.1:8000`.

### 🧩 Add and remove apps

```bash
uv run rusjango add app school
uv run rusjango remove app school
```

The removal command asks for confirmation. Use `--yes` to skip it deliberately.

App names must be Python identifiers beginning with a letter or underscore. `apps` and `rusjango` are reserved. Symlinked app removal is refused.

### 🗃️ Enable and disable ORM

```bash
uv run rusjango add orm
uv run rusjango migrate
```

```bash
uv run rusjango remove orm
```

Disabling ORM preserves models, schemas, API code, migration scaffold, and data. Adapt ORM-dependent handlers yourself.

> 💡 **Migrate is table creation:** It does not alter columns, rename tables, move data, or maintain migration history.

## 📁 Project detection

Commands find a parent `pyproject.toml` containing:

```toml
[tool.rusjango]
settings = "settings.py"
app = "main:app"
```

The configured settings path is respected. The standard scaffold uses `main.py` and an application object named `app`.

Changing the CLI settings path also requires changing the application's explicit `Rusjango(settings=...)` argument.

## ✍️ What scaffolding preserves

| Action | Preservation behavior |
|---|---|
| Add an app | Keeps unrelated settings and existing app packages |
| Add ORM | Adds missing models/schemas; upgrades only the exact untouched starter API |
| Add another app after ORM | Supplies ORM starter files for the new app |
| Remove ORM | Keeps application files and database data |

The settings editor supports literal string lists and dictionary/None database assignments. Computed values are rejected before app/ORM scaffolding. Edited-value comments and formatting may change; unrelated file contents are preserved.

## 🦀 Rust CLI

Rust embeds templates at compile time, so its installed binary does not need a checkout. Dev/migrate prefer uv and fall back to Python when uv is unavailable.

The Python package includes the full Python CLI; the separate Rust binary is optional.

## 🧭 Commands still pending

Auth, admin, Docker, application test scaffolding, workers, AI, and payments commands are not implemented.

---

[← Middleware](07-middleware.md) · [📚 Documentation home](README.md) · [Source development →](10-contributing.md)
