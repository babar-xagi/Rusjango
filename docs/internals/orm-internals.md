# ORM Internals

A deep dive into how the Rusjango async ORM is implemented across the files in `python/rusjango/src/rusjango/orm/`.

---

## Overview

```
orm/
  __init__.py    ← public API exports
  model.py       ← ModelMeta metaclass; Model base class; _MODEL_REGISTRY
  fields.py      ← Field base class and concrete field types
  queryset.py    ← lazy QuerySet builder
  sql.py         ← pure SQL string + parameter generation
  connection.py  ← connection lifecycle; acquire() context manager
```

The key design principle is **separation of concerns**: SQL is generated in `sql.py` with no knowledge of database connections, and executed in `connection.py` with no knowledge of model structure. `queryset.py` orchestrates the two.

---

## Model metaclass (`model.py`)

### How `ModelMeta` works

`ModelMeta` is a custom metaclass that intercepts class creation for any class that subclasses `Model`. It runs at **import time**, not at runtime.

```python
class ModelMeta(type):
    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> type:
        fields: dict[str, Field] = {}

        # 1. Collect Field instances from the class body
        for key, value in list(namespace.items()):
            if isinstance(value, Field):
                value.name = key          # stamp the field with its attribute name
                fields[key] = value
                del namespace[key]        # remove from class namespace

        # 2. Build the class
        cls = super().__new__(mcs, name, bases, namespace)

        # 3. Store fields on the class (not as regular attributes)
        cls._fields = fields

        # 4. Register non-abstract models
        if name != "Model" and not namespace.get("_abstract", False):
            _MODEL_REGISTRY.append(cls)

        return cls
```

**Why remove fields from the namespace?**

If `IntField()` instances were left as class attributes, accessing `Student.age` on an **instance** would return the `Field` object rather than the stored value. By removing them from the namespace before the class is built, instance attributes (set in `__init__`) shadow nothing — `student.age = 20` works as expected.

### Model `__init__`

The generated `__init__` accepts keyword arguments matching declared field names:

```python
student = Student(name="Alice", age=20)
# Internally: self.__dict__["name"] = "Alice", self.__dict__["age"] = 20
```

Unknown keyword arguments are ignored silently to allow constructing models from raw DB rows that may include extra columns.

### `_MODEL_REGISTRY`

A module-level list that `migrate` / `init_db` iterate to create all tables:

```python
_MODEL_REGISTRY: list[type[Model]] = []
```

Every concrete `Model` subclass appends itself automatically. The `migrate` command calls:

```python
for model_cls in _MODEL_REGISTRY:
    sql = create_table_sql(model_cls)
    await conn.execute(sql)
```

---

## Table naming algorithm

The table name is derived deterministically from the model's module path and class name:

```
Module:  apps.school.models
Parts:   ["apps", "school", "models"]
Table:   parts[1] + "_" + ClassName.lower()
       = "school_" + "student"
       = "school_student"
```

Implementation:

```python
def table_name(model_cls: type) -> str:
    module_parts = model_cls.__module__.split(".")
    prefix = module_parts[1] if len(module_parts) > 1 else module_parts[0]
    return f"{prefix}_{model_cls.__name__.lower()}"
```

This mirrors Django's default `<app_label>_<model_name>` convention.

---

## Field types (`fields.py`)

All field types inherit from `Field`:

```python
class Field:
    name: str          # set by ModelMeta
    null: bool         # allow NULL in DB
    primary_key: bool  # is this the PK column?

    def db_type(self) -> str:
        """Returns the SQL column type string."""
        raise NotImplementedError
```

Concrete field types and their SQL column types:

| Python class | SQL type | Notes |
|---|---|---|
| `IntField` | `INTEGER` | Use `primary_key=True` for auto-increment PK |
| `CharField` | `TEXT` | No max_length enforcement (SQLite is typeless) |
| `BoolField` | `INTEGER` | Stored as `0` / `1` |
| `FloatField` | `REAL` | |
| `TextField` | `TEXT` | Alias for `CharField` for semantic clarity |
| `DateTimeField` | `TEXT` | ISO 8601 string; no ORM-level datetime parsing yet |

### Auto-primary-key

If no field has `primary_key=True`, `ModelMeta` injects a default `id` column:

```python
if not any(f.primary_key for f in fields.values()):
    fields["id"] = IntField(primary_key=True)
```

---

## SQL generation (`sql.py`)

`sql.py` contains only pure functions — no I/O, no database calls. Every function takes model metadata and returns `(sql_string, params_tuple)`.

### `quote_ident(name: str) -> str`

Wraps a column or table name in double quotes to handle reserved words and case:

```python
quote_ident("order")  # → '"order"'
quote_ident("id")     # → '"id"'
```

### `create_table_sql(model_cls) -> str`

Returns a `CREATE TABLE IF NOT EXISTS` statement. Never overwrites an existing table.

```sql
CREATE TABLE IF NOT EXISTS "school_student" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "age" INTEGER NOT NULL
);
```

### `insert_sql(model_cls, data: dict) -> tuple[str, tuple]`

Returns the INSERT statement and a tuple of parameter values:

```python
sql, params = insert_sql(Student, {"name": "Alice", "age": 20})
# sql    = 'INSERT INTO "school_student" ("name", "age") VALUES (?, ?)'
# params = ("Alice", 20)
```

### `select_sql(model_cls, filters: dict, limit: int | None) -> tuple[str, tuple]`

Returns a SELECT statement with an optional WHERE clause and LIMIT:

```python
sql, params = select_sql(Student, {"age__gte": 18}, limit=10)
# sql    = 'SELECT * FROM "school_student" WHERE "age" >= ? LIMIT 10'
# params = (18,)
```

### `update_sql(model_cls, pk_value, data: dict) -> tuple[str, tuple]`

```python
sql, params = update_sql(Student, pk_value=1, data={"age": 21})
# sql    = 'UPDATE "school_student" SET "age" = ? WHERE "id" = ?'
# params = (21, 1)
```

### `delete_sql(model_cls, pk_value) -> tuple[str, tuple]`

```python
sql, params = delete_sql(Student, pk_value=1)
# sql    = 'DELETE FROM "school_student" WHERE "id" = ?'
# params = (1,)
```

### `build_where(filters: dict, engine: str) -> tuple[str, tuple]`

Parses Django-style `field__lookup=value` filter kwargs into a WHERE clause fragment.

Supported lookups:

| Suffix | SQL operator | Example |
|---|---|---|
| *(none)* | `=` | `age=20` → `"age" = ?` |
| `__exact` | `=` | `age__exact=20` |
| `__gte` | `>=` | `age__gte=18` |
| `__lte` | `<=` | `age__lte=65` |
| `__gt` | `>` | `age__gt=0` |
| `__lt` | `<` | `age__lt=100` |

The `engine` parameter controls placeholder style:
- `"sqlite"` → `?` placeholders
- `"postgresql"` → `$1`, `$2`, … placeholders

---

## QuerySet (`queryset.py`)

`QuerySet` is **lazy**: it accumulates filter conditions and options, but does not execute any SQL until a terminal method is called.

```python
# No SQL executed yet:
qs = Student.filter(age__gte=18).filter(name="Alice")

# SQL executed here:
students = await qs.all()
```

### Chaining

Filter calls return a new `QuerySet` instance (immutable chain):

```python
@dataclass
class QuerySet:
    model_cls: type
    _filters: dict = field(default_factory=dict)
    _limit: int | None = None

    def filter(self, **kwargs) -> "QuerySet":
        return QuerySet(
            model_cls=self.model_cls,
            _filters={**self._filters, **kwargs},
            _limit=self._limit,
        )

    def limit(self, n: int) -> "QuerySet":
        return QuerySet(self.model_cls, self._filters, n)
```

### Terminal methods

These methods actually execute the SQL:

| Method | Returns | SQL |
|---|---|---|
| `await qs.all()` | `list[Model]` | `SELECT *` with filters |
| `await qs.get(**kw)` | `Model` | `SELECT *` + filter; raises `DoesNotExist` if 0 rows, `MultipleObjectsReturned` if >1 |
| `await qs.first()` | `Model \| None` | `SELECT * LIMIT 1` with filters |
| `await qs.count()` | `int` | `SELECT COUNT(*)` with filters |
| `await qs.delete()` | `int` (rows affected) | `DELETE` with filters |

---

## Connection management (`connection.py`)

### Module-level state

```python
_db_config: dict | None = None
_sqlite_conn = None         # aiosqlite.Connection
_pg_pool    = None          # asyncpg.Pool
```

These are intentionally module-level because there is one database per running application. The `configure_db` → `init_db` → `acquire` lifecycle enforces ordered access.

### Lifecycle

```
configure_db(config)   ← called at app startup from settings
      ↓
  init_db()            ← called on ASGI lifespan "startup" event
      │                   opens connection / pool
      │                   creates all tables (runs CREATE TABLE IF NOT EXISTS)
      ↓
  acquire()            ← context manager; yields a connection for one operation
      ↓
  close_db()           ← called on ASGI lifespan "shutdown" event
```

### `acquire()` — context manager

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def acquire():
    if _sqlite_conn is not None:
        yield _sqlite_conn
    elif _pg_pool is not None:
        async with _pg_pool.acquire() as conn:
            yield conn
    else:
        raise RuntimeError("Database not initialised. Call init_db() first.")
```

SQLite yields the single persistent connection directly (SQLite does not support concurrent writes, so a single connection is appropriate for development). PostgreSQL yields a connection from the pool.

### SQLite vs PostgreSQL differences

| Concern | SQLite | PostgreSQL |
|---|---|---|
| Library | `aiosqlite` | `asyncpg` |
| Placeholder | `?` | `$1`, `$2`, … |
| Connection model | Single persistent connection | Connection pool |
| Row return type | `aiosqlite.Row` (dict-like) | `asyncpg.Record` (dict-like) |
| AUTOINCREMENT | `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL` or `GENERATED ALWAYS AS IDENTITY` |

The SQL generation layer (`sql.py`) receives the `engine` string and uses the correct placeholder style. The execution layer (`connection.py`) handles the difference in result row types by normalising to `dict` before returning to the QuerySet.

---

## SQL injection prevention

All user-supplied values go into the `params` tuple and are passed to the database driver separately — they are **never** interpolated into the SQL string:

```python
# SAFE — parameterized:
sql    = 'SELECT * FROM "school_student" WHERE "name" = ?'
params = ("Alice'; DROP TABLE school_student; --",)
await cursor.execute(sql, params)

# NEVER done — string formatting:
# sql = f'SELECT * FROM "school_student" WHERE "name" = "{name}"'  # UNSAFE
```

The database driver handles escaping. The ORM never constructs SQL with f-strings or `%` formatting on user input.
