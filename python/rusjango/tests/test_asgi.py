"""ASGI routing and response tests."""

from __future__ import annotations

import pytest

from rusjango import Rusjango
from rusjango.exceptions import HTTPException

from conftest import call_asgi


@pytest.mark.asyncio
async def test_home_route() -> None:
    app = Rusjango()

    @app.get("/")
    async def home():
        return {"message": "Hello"}

    status, data = await call_asgi(app)
    assert status == 200
    assert data == {"message": "Hello"}


@pytest.mark.asyncio
async def test_path_param() -> None:
    app = Rusjango()

    @app.get("/items/{id}")
    async def item(id: int):
        return {"id": id}

    status, data = await call_asgi(app, path="/items/42")
    assert status == 200
    assert data["id"] == 42


@pytest.mark.asyncio
async def test_not_found() -> None:
    app = Rusjango()

    @app.get("/")
    async def home():
        return {}

    status, data = await call_asgi(app, path="/missing")
    assert status == 404
    assert data["error"] == "Not Found"


@pytest.mark.asyncio
async def test_post_json() -> None:
    app = Rusjango()

    @app.post("/items")
    async def create(data: dict):
        return {"created": data.get("name")}

    status, data = await call_asgi(
        app,
        method="POST",
        path="/items",
        body=b'{"name": "book"}',
    )
    assert status == 200
    assert data["created"] == "book"


@pytest.mark.asyncio
async def test_http_exception() -> None:
    app = Rusjango()

    @app.get("/fail")
    async def fail():
        raise HTTPException(418, detail="teapot")

    status, data = await call_asgi(app, path="/fail")
    assert status == 418
    assert data["detail"] == "teapot"
