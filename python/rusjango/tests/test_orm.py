"""ORM CRUD tests (SQLite)."""

from __future__ import annotations

import pytest

from rusjango.orm import Integer, Model, String, configure_db, close_db, init_db
from rusjango.orm.query import DoesNotExist


@pytest.fixture
async def db(tmp_path):
    import rusjango.orm.model as model_mod

    model_mod._MODEL_REGISTRY.clear()
    configure_db({"ENGINE": "sqlite", "NAME": str(tmp_path / "test.db"), "ASYNC": True})

    class Book(Model):
        id = Integer(primary_key=True)
        title = String(max_length=200)
        pages = Integer(nullable=True)

    await init_db()
    yield Book
    await close_db()
    model_mod._MODEL_REGISTRY.clear()


@pytest.mark.asyncio
async def test_create_and_get(db) -> None:
    Book = db
    book = await Book.create(title="Rusjango Guide", pages=120)
    assert book.title == "Rusjango Guide"
    assert book.id is not None

    found = await Book.get(id=book.id)
    assert found.title == "Rusjango Guide"


@pytest.mark.asyncio
async def test_filter_and_update(db) -> None:
    Book = db
    await Book.create(title="A", pages=10)
    await Book.create(title="B", pages=30)

    rows = await Book.filter(pages__gte=20).all()
    assert len(rows) == 1
    assert rows[0].title == "B"

    await Book.filter(id=rows[0].id).update(title="B updated")
    updated = await Book.get(id=rows[0].id)
    assert updated.title == "B updated"


@pytest.mark.asyncio
async def test_delete(db) -> None:
    Book = db
    b = await Book.create(title="Delete me", pages=1)
    await Book.filter(id=b.id).delete()
    with pytest.raises(DoesNotExist):
        await Book.get(id=b.id)
