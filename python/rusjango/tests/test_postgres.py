"""Real PostgreSQL checks. Use a disposable database with the DSN below."""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest

from rusjango.orm import (
    Boolean,
    Integer,
    Model,
    String,
    close_db,
    configure_db,
    init_db,
)
from rusjango.orm import connection, model as model_module, sql


@pytest.fixture
async def postgres_models():
    dsn = os.environ.get("RUSJANGO_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip(
            "Set RUSJANGO_TEST_POSTGRES_DSN to test a disposable PostgreSQL database"
        )
    pytest.importorskip("asyncpg")
    previous = model_module._MODEL_REGISTRY[:]
    model_module._MODEL_REGISTRY.clear()
    await close_db()
    configure_db({"ENGINE": "postgresql", "URL": dsn, "MIN_SIZE": 1, "MAX_SIZE": 2})
    suffix = uuid.uuid4().hex

    class Book(Model):
        _table = "rusjango_test_book_" + suffix
        id = Integer(primary_key=True)
        title = String(unique=True)
        active = Boolean(default=True)

    class Receipt(Model):
        _table = "rusjango_test_receipt_" + suffix
        id = Integer(primary_key=True)

    try:
        await init_db()
        yield Book, Receipt
    finally:
        for model in (Book, Receipt):
            await connection.execute(
                f"DROP TABLE IF EXISTS {sql.quote_ident(model._table, 'postgresql')}"
            )
        await close_db()
        configure_db(None)
        model_module._MODEL_REGISTRY[:] = previous


async def test_postgres_crud_defaults_and_pool_reuse(postgres_models):
    Book, Receipt = postgres_models
    books = await asyncio.gather(*(Book.create(title=f"book-{i}") for i in range(12)))
    assert len({book.id for book in books}) == 12
    assert all(book.active is True for book in books)
    receipt = await Receipt.create()
    assert receipt.id is not None
    assert await Book.filter(id=books[0].id).update(title="updated", active=False) == 1
    assert (await Book.get(id=books[0].id)).active is False
    assert await Book.filter(id__gte=0).delete() == 12
    pool = await connection._pg_pool_get()
    assert pool.get_idle_size() == pool.get_size()


async def test_postgres_connection_reusable_after_constraint_error(postgres_models):
    Book, _ = postgres_models
    await Book.create(title="unique")
    import asyncpg

    with pytest.raises(asyncpg.UniqueViolationError):
        await Book.create(title="unique")
    assert (await Book.create(title="after-error")).id is not None
