# 🧩 Organize your API into apps

**Rusjango 0.1.5 · Alpha**

An application groups related endpoints into its own Python package. This tutorial continues inside the `demo` project from [First steps](02-getting-started.md).

## 📁 Create an app

Stop the development server, then:

```bash
uv run rusjango add app school
```

The CLI creates:

```text
apps/
├── __init__.py
└── school/
    ├── __init__.py
    └── api.py
```

It also adds `"apps.school"` to `INSTALLED_APPS`.

## 🌐 Understand the router

The starter `apps/school/api.py` contains:

```python
from rusjango import Router

router = Router()


@router.get("/students")
async def list_students():
    return [{"name": "Ali"}, {"name": "Sara"}]
```

With `app.load_installed_apps()` in `main.py`, the route is mounted at:

```text
GET /api/school/students
```

Restart the server:

```bash
uv run rusjango dev
```

Then:

```bash
curl http://127.0.0.1:8000/api/school/students
```

```json
[{"name": "Ali"}, {"name": "Sara"}]
```

> 💡 **The prefix comes from the app name:** Write `/students` inside the router. Rusjango adds `/api/school` when it mounts the app.

## ➕ Add another app

```bash
uv run rusjango add app library
```

The independent `library` router is mounted under `/api/library/`. Each app must create a fresh `Router()` to keep its route table separate.

Use the `Router` class shown above for multi-app projects. The exported singleton `router` is intended as a single-file convenience.

## ✍️ Add a custom route

Add this to `apps/library/api.py`:

```python
@router.get("/about")
async def about():
    return {"app": "library"}
```

It becomes `GET /api/library/about`.

If you later run `add orm`, a custom API file is preserved. The CLI adds missing model/schema files and only upgrades an API that exactly matches the untouched starter.

## 🔌 Mount a router manually

For a standalone application:

```python
from rusjango import Router, Rusjango

app = Rusjango()
catalog = Router()


@catalog.get("/items")
async def list_items():
    return []


app.include_router(catalog, prefix="/api/catalog")
```

The endpoint is `GET /api/catalog/items`. Manual mounting does not require an `INSTALLED_APPS` entry.

## 🗃️ Apps with ORM enabled

When a database is already configured, newly added apps receive model/schema starter files and an ORM starter API.

The [next guide](05-orm-guide.md) uses the untouched school starter so that `add orm` can upgrade it. The custom library API stays intact if you keep that app; adapt it manually when it needs database access.

## 🗑️ Remove an app

Stop the server before changing app files:

```bash
uv run rusjango remove app library
```

The CLI asks for confirmation, unregisters the app, and deletes its package. Use `--yes` only when you intend to skip that prompt.

> 📌 **Removal scope:** App removal does not drop database tables. ORM removal keeps model/schema/API files. Both operations may require you to adapt imports and handlers.

Removing a symlinked app is refused. App names must be Python identifiers; `apps` and `rusjango` are reserved.

---

[← Schemas](08-schema-validation.md) · [📚 Documentation home](README.md) · [Next: Async ORM →](05-orm-guide.md)
