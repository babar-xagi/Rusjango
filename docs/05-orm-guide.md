# ORM Guide

Rusjango ships a lightweight async ORM built on top of `aiosqlite` (SQLite) and `asyncpg` (PostgreSQL). It follows a Django-inspired API — model classes, querysets, and field descriptors — while staying fully async.

---

## Enabling the ORM

```bash
rusjango add orm   # configures settings.py, creates migrations/, adds aiosqlite
rusjango migrate   # creates tables in the database
```

If you already have apps, `rusjango add orm` also scaffolds `models.py`, `schemas.py`, and upgrades `api.py` in each one. See the [CLI reference](./03-cli-reference.md#rusjango-add-orm) for the full list of changes.

---

## Model definition

```python
# apps/school/models.py
from rusjango.orm import Model, Integer, String, Text, Boolean

class Student(Model):
    id = Integer(primary_key=True)
    name = String(max_length=100)
    age = Integer(nullable=True)
    bio = Text(nullable=True)
    active = Boolean(default=True)
```

Fields are declared as class-level attributes. The `ModelMeta` metaclass collects them at class-creation time and removes them from the class namespace, so accessing `student.name` reads the instance attribute set by the ORM, not the field descriptor.

---

## Field types

| Field class | Python type | SQL type (SQLite) | SQL type (PostgreSQL) | Options |
|---|---|---|---|---|
| `Integer` | `int` | `INTEGER` | `INTEGER` | `primary_key`, `nullable`, `default` |
| `String` | `str` | `VARCHAR(n)` | `VARCHAR(n)` | `max_length` (default 255), `nullable`, `unique` |
| `Text` | `str` | `TEXT` | `TEXT` | `nullable` |
| `Boolean` | `bool` | `INTEGER` (0/1) | `BOOLEAN` | `nullable`, `default` |

### Common field options

| Option | Type | Default | Description |
|---|---|---|---|
| `primary_key` | `bool` | `False` | Marks the column as `INTEGER PRIMARY KEY AUTOINCREMENT` (SQLite) or `INTEGER PRIMARY KEY` (PostgreSQL) |
| `nullable` | `bool` | `False` | Allows `NULL` in the column. Omitting it makes the column `NOT NULL` |
| `unique` | `bool` | `False` | Adds a `UNIQUE` constraint (not applied to primary key columns) |
| `default` | `Any` | `None` | Python-side default value used during `Model.create()` when the field is omitted |
| `max_length` | `int` | `255` | Column width for `String` (mapped to `VARCHAR(n)`) |

> **Boolean on SQLite:** SQLite has no native boolean type. Rusjango stores `True` as `1` and `False` as `0` (`INTEGER`). When reading rows back, the ORM converts the integer to `bool` automatically via `_from_row`.

---

## Table naming

Table names are derived automatically from the model's module path:

| Module path | Class name | Table name |
|---|---|---|
| `apps.school.models` | `Student` | `school_student` |
| `apps.billing.models` | `Invoice` | `billing_invoice` |
| Any other module | `MyModel` | `mymodel` (class name lowercased) |

The rule for app-scoped models: `apps.<app>.<ModelName>` → `<app>_<modelname_lower>`.

To override the table name, set `_table` on the class:

```python
class Student(Model):
    _table = "enrollment_students"
    id = Integer(primary_key=True)
    name = String(max_length=100)
```

---

## Create

```python
student = await Student.create(name="Ali", age=20)
print(student.id)    # auto-assigned from last_insert_rowid() on SQLite
print(student.name)  # "Ali"
```

`create()` builds an `INSERT` statement from the provided keyword arguments. Fields that are omitted but have a `default` value use the default. The primary key is fetched after insert via `SELECT last_insert_rowid()` (SQLite) and set on the returned instance.

Fields that are neither provided, nor have a default, nor are `nullable` raise a `ValueError` before any SQL is run:

```python
# Missing required field "name" → ValueError: Missing required field: name
student = await Student.create(age=20)
```

---

## Get one

```python
student = await Student.get(id=1)
```

Returns exactly one instance matching the given filters. Raises:

- `rusjango.orm.DoesNotExist` — if no row matched.
- `rusjango.orm.MultipleObjectsReturned` — if more than one row matched.

```python
from rusjango.orm import DoesNotExist, MultipleObjectsReturned

try:
    student = await Student.get(name="Ali")
except DoesNotExist:
    # handle missing
    ...
except MultipleObjectsReturned:
    # handle ambiguous
    ...
```

---

## Filter and list

### All rows

```python
students = await Student.all()
# → list[Student]
```

### Filter with conditions

```python
students = await Student.filter(age__gte=18).all()
```

### First matching row

```python
first = await Student.filter(name="Ali").first()
# → Student | None  (None if no rows match)
```

### Chaining filters

Filters can be chained; each call returns a new `QuerySet`:

```python
qs = Student.filter(active=True).filter(age__gte=18)
results = await qs.all()
```

---

## Filter lookups

Filters use a `field__lookup=value` syntax. A plain `field=value` is equivalent to `field__exact=value`.

| Lookup | SQL operator | Example |
|---|---|---|
| `exact` (default) | `=` | `Student.filter(age=20)` |
| `gte` | `>=` | `Student.filter(age__gte=18)` |
| `lte` | `<=` | `Student.filter(age__lte=30)` |
| `gt` | `>` | `Student.filter(age__gt=17)` |
| `lt` | `<` | `Student.filter(age__lt=65)` |

Multiple filters in a single call are combined with `AND`:

```python
await Student.filter(age__gte=18, active=True).all()
# WHERE "age" >= ? AND "active" = ?
```

An unsupported lookup suffix raises `ValueError` immediately.

---

## Update

```python
await Student.filter(id=1).update(name="Ahmed")
```

`update()` requires at least one filter. Calling it on an unfiltered queryset raises:

```
ValueError: update() requires at least one filter
```

Multiple fields can be updated at once:

```python
await Student.filter(active=False).update(active=True, age=0)
```

`update()` returns `1` (a placeholder; row-count tracking is planned for a future release).

---

## Delete

```python
await Student.filter(id=1).delete()
```

Like `update()`, `delete()` requires at least one filter:

```
ValueError: delete() requires at least one filter
```

This prevents accidental full-table deletes. `delete()` returns `1` (placeholder).

---

## Reading rows

Model instances expose all fields as regular attributes set by `__init__`:

```python
student = await Student.get(id=1)
print(student.id)     # int
print(student.name)   # str
print(student.active) # bool (converted from SQLite INTEGER automatically)
```

### `to_dict()`

Converts an instance back to a plain dict:

```python
data = student.to_dict()
# {"id": 1, "name": "Ali", "age": 20, "bio": None, "active": True}
```

Useful for constructing `Schema` output objects:

```python
StudentOut.from_dict(student.to_dict()).dict()
```

---

## Connection settings (`settings.py`)

### SQLite (default)

Added automatically by `rusjango add orm`:

```python
DATABASE = {
    "ENGINE": "sqlite",
    "NAME": "db.sqlite3",   # path to the database file
    "ASYNC": True,
}
```

The `"ASYNC": True` key is informational — Rusjango's ORM is always async.

### PostgreSQL

```python
DATABASE = {
    "ENGINE": "postgresql",
    "URL": "postgresql://user:pass@localhost:5432/dbname",
    "ASYNC": True,
}
```

PostgreSQL support requires `asyncpg`:

```bash
uv add asyncpg
```

`asyncpg` uses `$1`, `$2`, ... positional placeholders; the ORM handles this automatically based on `engine_name()`.

---

## Migrations

Rusjango's current migration system is intentionally minimal:

```bash
rusjango migrate
```

This runs `python -m rusjango._migrate`, which:

1. Reads `DATABASE` from `settings.py`.
2. Imports every `<app>.models` module listed in `INSTALLED_APPS` to register model classes.
3. Calls `CREATE TABLE IF NOT EXISTS` for each registered model.

**Safe to run multiple times** — if a table already exists the statement is a no-op.

**Limitations:**

- No field-level migration tracking. If you add or rename a column in a model, `rusjango migrate` will not alter the existing table.
- No `ALTER TABLE`, no rollback, no migration history file.
- Full field-level migrations (with tracking and rollback) are planned for Phase 3.x.

**Workaround for schema changes (current):** Drop the table manually and re-run `rusjango migrate`, or write raw SQL alter statements and apply them directly.

---

## Using the ORM in API handlers

The typical pattern in `apps/<name>/api.py`:

```python
from rusjango import Router, HTTPException
from rusjango.orm import DoesNotExist

from .models import Student
from .schemas import StudentCreate, StudentOut

router = Router()


@router.get("/students")
async def list_students():
    students = await Student.all()
    return [StudentOut.from_dict(s.to_dict()).dict() for s in students]


@router.get("/students/{id}")
async def get_student(id: int):
    try:
        student = await Student.get(id=id)
    except DoesNotExist:
        raise HTTPException(404, detail=f"Student {id} not found")
    return StudentOut.from_dict(student.to_dict()).dict()


@router.post("/students")
async def create_student(data: StudentCreate):
    student = await Student.create(name=data.name, age=data.age)
    return StudentOut.from_dict(student.to_dict()).dict()


@router.delete("/students/{id}")
async def delete_student(id: int):
    try:
        await Student.get(id=id)          # verify existence first
    except DoesNotExist:
        raise HTTPException(404, detail=f"Student {id} not found")
    await Student.filter(id=id).delete()
    return None                            # 204 No Content
```

---

## ORM internals

A brief map of the source files under `rusjango/orm/`:

| File | Responsibility |
|---|---|
| `fields.py` | `Field` base class and concrete field types (`Integer`, `String`, `Text`, `Boolean`). Each field knows its SQL type per engine via `sql_type(engine)`. |
| `model.py` | `ModelMeta` metaclass collects `Field` instances from the class body, strips them from the namespace, and sets `cls._fields`. `_MODEL_REGISTRY` is a module-level list that `init_db` iterates. `_default_table_name` derives the table name from the module path. |
| `query.py` | `QuerySet` holds a model class and a filter dict. `.all()`, `.first()`, `.get()` call `_fetch()` which delegates to `sql.select_sql` + `connection.fetchall`. `.update()` and `.delete()` call their respective sql helpers. |
| `sql.py` | Pure SQL generation — `create_table_sql`, `insert_sql`, `select_sql`, `update_sql`, `delete_sql`, and `build_where`. `build_where` parses `field__lookup=value` keys into `WHERE` clauses with positional parameters (`?` for SQLite, `$n` for PostgreSQL). |
| `connection.py` | Manages a single shared `aiosqlite` connection (SQLite) or an `asyncpg` connection pool (PostgreSQL). `configure_db(config)` sets the global config dict. `execute`, `fetchall`, `fetchone` are the low-level async primitives used by the query layer. `init_db` and `close_db` are lifecycle helpers. |
| `__init__.py` | Public re-exports: `Model`, `Field`, `Integer`, `String`, `Boolean`, `Text`, `configure_db`, `init_db`, `close_db`, `DoesNotExist`, `MultipleObjectsReturned`. |

### Model registration flow

```mermaid
graph TD
    A[class Student defined]:::accent0
    B[ModelMeta.__new__ runs]:::accent1
    C[Field instances collected into _fields]:::accent2
    D[Student added to _MODEL_REGISTRY]:::accent3
    E[rusjango migrate called]:::accent4
    F[_load_models imports apps.school.models]:::accent5
    G[init_db iterates _MODEL_REGISTRY]:::accent6
    H[CREATE TABLE IF NOT EXISTS school_student]:::accent7

    A --> B --> C --> D
    E --> F --> D
    D --> G --> H
```
