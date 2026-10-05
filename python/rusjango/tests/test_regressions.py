"""Regression tests for the Phase 1–3 review findings."""

from __future__ import annotations

import asyncio

import pytest

from rusjango import Rusjango, Schema
from rusjango.orm import Integer, Model, String, close_db, configure_db, init_db
from rusjango.orm import connection, sql
from conftest import call_asgi


async def exchange(app, scope, events=()):
    messages = []
    incoming = iter(events)

    async def receive():
        return next(incoming)

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    return messages


def http_scope(path="/", method="GET", host="localhost"):
    return {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [(b"host", host.encode())],
    }


@pytest.mark.parametrize("path", ["/files/reportXjson", "/files/report-json"])
async def test_route_literals_are_not_regex(path):
    app = Rusjango()

    @app.get("/files/report.json")
    async def report():
        return {"ok": True}

    assert (await call_asgi(app, path=path))[0] == 404


async def test_invalid_and_missing_parameters_are_client_errors():
    app = Rusjango()

    @app.get("/items/{id}")
    async def item(id: int, limit: int):
        return {"id": id, "limit": limit}

    assert (await call_asgi(app, path="/items/nope", query="limit=1"))[0] == 422
    assert (await call_asgi(app, path="/items/1"))[0] == 422


async def test_wrong_method_returns_allow_header():
    app = Rusjango()

    @app.get("/")
    async def home():
        return {}

    messages = await exchange(app, http_scope(method="POST"))
    assert messages[0]["status"] == 405
    assert b"GET" in dict(messages[0]["headers"])[b"allow"]


async def test_no_content_has_no_body():
    app = Rusjango()

    @app.delete("/")
    async def delete():
        return None

    messages = await exchange(app, http_scope(method="DELETE"))
    assert messages[0]["status"] == 204
    assert messages[1]["body"] == b""


async def test_security_settings_available_before_middleware():
    app = Rusjango()
    app.settings = {
        "DEBUG": False,
        "ALLOWED_HOSTS": ["good.example"],
        "MIDDLEWARE": ["rusjango.security.SecurityMiddleware"],
    }

    @app.get("/")
    async def home():
        return {}

    messages = await exchange(app, http_scope(host="evil.example"))
    assert messages[0]["status"] == 400
    assert dict(messages[0]["headers"])[b"x-frame-options"] == b"DENY"


async def test_lifespan_acknowledges_startup_and_shutdown():
    messages = await exchange(
        Rusjango(),
        {"type": "lifespan"},
        [
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ],
    )
    assert messages == [
        {"type": "lifespan.startup.complete"},
        {"type": "lifespan.shutdown.complete"},
    ]


class PersonInput(Schema):
    age: int


@pytest.mark.parametrize("body", [b"{}", b'{"age":"wrong"}', b"[]", b"null"])
async def test_invalid_schema_body_returns_422(body):
    app = Rusjango()

    @app.post("/")
    async def create(data: PersonInput):
        return data.dict()

    assert (await call_asgi(app, method="POST", body=body))[0] == 422


@pytest.fixture
async def isolated_db():
    import rusjango.orm.model as models

    previous = models._MODEL_REGISTRY[:]
    models._MODEL_REGISTRY.clear()
    await close_db()
    configure_db({"ENGINE": "sqlite", "NAME": ":memory:"})
    yield
    await close_db()
    configure_db(None)
    models._MODEL_REGISTRY[:] = previous


async def test_distinct_models_have_distinct_tables(isolated_db):
    class Student(Model):
        id = Integer(primary_key=True)
        name = String()

    class Invoice(Model):
        id = Integer(primary_key=True)
        amount = Integer()

    assert Student._table != Invoice._table
    await init_db()
    student = await Student.create(name="Ali")
    invoice = await Invoice.create(amount=10)
    assert (await Student.get(id=student.id)).name == "Ali"
    assert (await Invoice.get(id=invoice.id)).amount == 10


async def test_concurrent_create_returns_own_primary_key(isolated_db):
    class Book(Model):
        id = Integer(primary_key=True)
        title = String()

    await init_db()
    created = await asyncio.gather(*(Book.create(title=str(i)) for i in range(20)))
    stored = {row.title: row.id for row in await Book.all()}
    assert len({row.id for row in created}) == 20
    assert all(stored[row.title] == row.id for row in created)


async def test_update_delete_report_actual_affected_rows(isolated_db):
    class Book(Model):
        id = Integer(primary_key=True)
        title = String()

    await init_db()
    await Book.create(title="A")
    await Book.create(title="A")
    assert await Book.filter(title="A").update(title="B") == 2
    assert await Book.filter(title="missing").delete() == 0
    assert await Book.filter(title="B").delete() == 2


async def test_failed_insert_rolls_back_and_null_filters_work(isolated_db):
    class Book(Model):
        id = Integer(primary_key=True)
        title = String(unique=True)
        pages = Integer(nullable=True)

    await init_db()
    await Book.create(title="unique")
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        await Book.create(title="unique")
    assert (await Book.create(title="next")).id is not None
    assert len(await Book.filter(pages=None).all()) == 2


async def test_lifespan_closes_open_database(isolated_db):
    app = Rusjango()
    app.settings = {"DATABASE": {"ENGINE": "sqlite", "NAME": ":memory:"}}
    await connection.execute('CREATE TABLE "example" ("id" INTEGER)')
    await exchange(
        app,
        {"type": "lifespan"},
        [
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ],
    )
    assert connection._sqlite_conn is None


def test_postgres_update_uses_separate_parameters():
    configure_db({"ENGINE": "postgresql", "URL": "unused"})
    try:
        where, params = sql.build_where({"id": 3}, "postgresql")
        query, values = sql.update_sql("books", {"title": "new"}, where, params)
        assert query == 'UPDATE "books" SET "title" = $1 WHERE "id" = $2'
        assert values == ["new", 3]
    finally:
        configure_db(None)


async def test_postgres_connection_released_even_on_error(monkeypatch):
    class Pool:
        def __init__(self):
            self.conn = object()
            self.released = []

        async def acquire(self):
            return self.conn

        async def release(self, conn):
            self.released.append(conn)

    pool = Pool()
    configure_db({"ENGINE": "postgresql", "URL": "unused"})
    monkeypatch.setattr(connection, "_pg_pool", pool)
    try:
        with pytest.raises(RuntimeError, match="handler failed"):
            async with connection.acquire():
                raise RuntimeError("handler failed")
        assert pool.released == [pool.conn]
    finally:
        monkeypatch.setattr(connection, "_pg_pool", None)
        configure_db(None)
