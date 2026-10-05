# Async ORM

Applies to Rusjango 0.1.4 (alpha).

Enable with `rusjango add orm`, then run `rusjango migrate` explicitly.

```python
from rusjango.orm import Model, Integer, String, Boolean

class Book(Model):
    id = Integer(primary_key=True)
    title = String(max_length=200, unique=True)
    active = Boolean(default=True)
```

Integer, String, Text, and Boolean fields support primary_key, nullable, unique, and default. String also has max_length. Defaults are applied by create; callable defaults are called for each insert. SQLite does not enforce VARCHAR length. Schema validation is separate from ORM/database constraints.

App models use `<app>_<class_lowercase>` table names; other models use the lowercased class name. Override with `_table`. Every concrete subclass gets its own default table name. At most one primary key is supported; it must be declared explicitly.

```python
book = await Book.create(title='Hello')
book = await Book.get(id=book.id)
books = await Book.filter(active=True).filter(id__gte=1).all()
first = await Book.filter(active=True).first()
changed = await Book.filter(id=book.id).update(title='Updated')
deleted = await Book.filter(id=book.id).delete()
```

get raises DoesNotExist or MultipleObjectsReturned. first returns None if absent. update/delete return actual affected-row counts and require a filter. Unknown field names are rejected. Lookups: exact, gte, lte, gt, lt; `field=None` produces IS NULL.

Generated integer primary keys work on SQLite and PostgreSQL. INSERT RETURNING reads the inserted row atomically, including defaults and nullable fields. SQLite requires 3.35+.

## Backends

```python
DATABASE = {'ENGINE': 'sqlite', 'NAME': 'db.sqlite3'}
# Install rusjango[postgres] for the PostgreSQL driver:
DATABASE = {'ENGINE': 'postgresql', 'URL': 'postgresql://user:pass@localhost/db',
            'MIN_SIZE': 1, 'MAX_SIZE': 10}
```

One database per process. Connections open lazily and close during ASGI shutdown or via close_db. Close the current database before reconfiguration. PostgreSQL pool connections are returned after each operation, including errors.

## Migrations and limits

`migrate` uses CREATE TABLE IF NOT EXISTS. It does not change an existing table. There are no relationships, transaction API, migration history/rollback, ordering, pagination, joins, or count API.

Older versions incorrectly put default models into a table named `model`. Corrected names do not automatically recover that data. Back up existing data, inspect the old table, and move rows with explicit SQL before switching a deployed application.
