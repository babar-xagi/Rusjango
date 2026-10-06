# 🛡️ Admin foundations

**Rusjango 0.1.6 · Alpha**

Register models, choose visible fields, and work with permission-gated data from trusted server code.

> 📌 **Phase 5 is a backend foundation.** It installs no HTTP routes, dashboard, login, session, or authentication provider. `/admin` returns 404 unless your application defines that route. Authentication and browser integration are later work.

## 🚀 1. Add the scaffold

Start with the [school application and ORM](05-orm-guide.md), then run:

```bash
uv run rusjango add admin
```

This creates `admin.py` with a synchronous `create_site(app)` factory. It preserves settings and dependencies.

Enable the factory in `settings.py`:

```python
ADMIN = {"FACTORY": "admin:create_site"}
```

Keep `app.load_installed_apps()` in `main.py`. It creates the site, imports optional admin modules from installed applications, and makes the site available as `app.admin_site`.

## 🧩 2. Register a model

Create `apps/school/admin.py`:

```python
from .models import Student


def register(site):
    site.register(
        Student,
        list_display=("id", "name", "age"),
        detail_fields=("id", "name", "age"),
        list_filter=("age",),
        search_fields=("name",),
        sortable_fields=("id", "name", "age"),
        page_size=25,
    )
```

The generated Student model has an integer primary key, name, and age. Its default admin label is `school.student`; this label identifies permissions and services, and is independent of the SQL table name.

Registration requires an explicit list of visible fields and one declared primary key. Include that key in both list and detail fields. Unlisted fields are absent from returned data. Filters, search, and sorting can use only explicitly exposed detail fields.

Models are read-only by default. A grant alone cannot enable creation, updates, or deletion.

## 🔒 3. Supply a trusted identity

The following example is for a trusted server process after establishing who its caller is:

```python
from rusjango.admin import AdminIdentity

reader = AdminIdentity(
    subject="operator-42",
    permissions={"admin:school.student:view"},
)
```

`AdminIdentity` records an already trusted subject and its grants. It does not check a password, authenticate a token, or verify identity. Never construct it from user-submitted subjects or permission lists.

Grants are exact strings, with no wildcard or implicit administrator role:

| Grant | Allows |
|---|---|
| `admin:school.student:view` | Catalog visibility, lists, and details |
| `admin:school.student:add` | Creation when a create schema is configured; also needs view |
| `admin:school.student:change` | Updates when an update schema is configured; also needs view |
| `admin:school.student:delete` | Deletion when `allow_delete=True` |

Missing identities and missing grants raise `AdminPermissionDenied` before database access. The catalog returns only models visible to that identity.

## 🔎 4. Read records

Inside an async server function, after configuring the database:

```python
site = app.admin_site

catalog = site.catalog(identity=reader)

page = await site.list(
    "school.student",
    identity=reader,
    limit=20,
    offset=0,
    sort="name",
    filters={"age__gte": 18},
    search="sa",
)

student = await site.detail("school.student", 1, identity=reader)
```

A list response contains `model`, `items`, `columns`, `limit`, `offset`, and `has_more`. A detail response is a dictionary of configured detail fields.

- Limit is 1–100; offset is 0–10,000. The configured page size defaults to 25.
- Sort uses a configured field; prefix `-` for descending. The primary key breaks ties and is the default order.
- Filter operations are exact, `__gte`, `__gt`, `__lte`, and `__lt`. Values use strict ORM field types. Exact `None` filters require a nullable field.
- Search is at most 256 characters and matches case-insensitive literal substrings across configured string fields. SQL wildcard characters are escaped.
- Queries parameterize values and select only configured output columns.

Missing records raise `rusjango.orm.DoesNotExist`. Invalid options raise `ValueError` or `TypeError`; invalid field values raise `SchemaValidationError`. These are service exceptions, with no HTTP response mapping yet.

## ✍️ 5. Enable specific writes

Replace the registration module with the following, then restart the server or reload your Python process to apply it:

```python
from rusjango import Field, Schema

from .models import Student


class StudentCreate(Schema):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)


class StudentRename(Schema):
    name: str = Field(min_length=1, max_length=100)


def register(site):
    site.register(
        Student,
        list_display=("id", "name", "age"),
        create_schema=StudentCreate,
        update_schema=StudentRename,
        allow_delete=True,
    )
```

Use a trusted identity with the corresponding grants:

```python
editor = AdminIdentity(
    subject="operator-42",
    permissions={
        "admin:school.student:view",
        "admin:school.student:add",
        "admin:school.student:change",
        "admin:school.student:delete",
    },
)

created = await site.create(
    "school.student", {"name": "Sara", "age": 22}, identity=editor
)
renamed = await site.update(
    "school.student", created["id"], {"name": "Sarah"}, identity=editor
)
deleted_count = await site.delete(
    "school.student", created["id"], identity=editor
)
```

The schema defines editable fields; you can further restrict them with `editable_fields`. Primary keys cannot be edited. Unknown input fields are rejected, including fields outside that operation's schema.

Create schemas must cover required ORM fields and currently require a generated integer primary key. Schema types must match scalar ORM types; nullable schema values require nullable ORM fields. Specify constraints explicitly in schemas, including string lengths appropriate for PostgreSQL.

Updates validate the complete update schema and apply its defaults; they are not partial PATCH validation. A narrow schema such as StudentRename changes only its declared fields. Create/update return projected detail data and therefore also require view permission.

The catalog includes write capabilities and authorized form metadata: field names, scalar types, nullability, required flags, and Field constraints. It never includes schema default values.

## ⚙️ Factory and discovery rules

Each application instance owns an independent AdminSite. The default factory can also register models directly.

`load_installed_apps()` calls `load_admin()`; you can call `load_admin()` explicitly after configuring installed packages. Repeated loads reuse the site's factory result and do not duplicate successful registrations. Every discovered `<installed_package>.admin` module must define synchronous `register(site)`.

Missing admin modules are optional. Missing dependencies inside a module and broken registrations are reported. A failed registration rolls back its registry changes. Async factories and callbacks are rejected.

`ADMIN` accepts `None` or exactly `{"FACTORY": "module:callable"}`. The synchronous factory receives the application and must return an AdminSite.

## 🧹 Remove the scaffold

Set `ADMIN = None` in your settings before removing its referenced factory:

```bash
uv run rusjango remove admin
```

Removal prompts for confirmation. `--yes` skips the prompt. Only an unchanged tracked `admin.py` is deleted; edited files and per-app registration modules remain. Base settings and dependency files remain intact, so update stale factory references yourself.

## 🧭 Current boundaries

This foundation has model-level grants. It has no tenant/row policies, audit trail, CSRF protection, authentication adapter, or browser routes. The ORM still uses one process-wide backend and offers no transaction API. Update followed by detail lookup is not an atomic operation.

Keep these services inside trusted server code until authentication and the HTTP security boundary are implemented. See [Phase 5 validation](18-phase5-validation.md) for tested behavior.

---

[← Application tests](15-testing.md) · [📚 Documentation home](README.md) · [Settings reference](06-settings-reference.md)
