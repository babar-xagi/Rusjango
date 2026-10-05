"""Validation contract for supported Schema annotations."""

from __future__ import annotations

import pytest

from rusjango import Schema, Rusjango
from rusjango.schema import SchemaValidationError
from conftest import call_asgi


class Address(Schema):
    city: str


class Person(Schema):
    name: str
    age: int | None = None
    address: Address | None = None
    tags: list[str] = []


def test_defaults_are_independent_and_extras_ignored():
    first = Person.from_dict({"name": "Ali", "extra": True})
    second = Person(name="Sara")
    first.tags.append("student")
    assert second.tags == []
    assert second.dict() == {"name": "Sara", "age": None, "address": None, "tags": []}


def test_nested_schemas_serialize():
    person = Person(name="Ali", address={"city": "Lahore"})
    assert isinstance(person.address, Address)
    assert person.dict()["address"] == {"city": "Lahore"}


@pytest.mark.parametrize("value", [True, "20", 20.5])
def test_integer_fields_are_strict(value):
    with pytest.raises(SchemaValidationError):
        Person(name="Ali", age=value)


def test_list_error_identifies_element():
    with pytest.raises(SchemaValidationError) as error:
        Person(name="Ali", tags=["ok", 3])
    assert error.value.errors[0]["loc"] == ["tags", 1]


async def test_schema_body_with_optional_query_and_query_name_collision():
    app = Rusjango()

    @app.post("/")
    async def create(data: Person, limit: int = 10):
        return {"person": data.dict(), "limit": limit}

    status, data = await call_asgi(
        app, method="POST", query="data=ignored", body=b'{"name":"Ali"}'
    )
    assert status == 200
    assert data["limit"] == 10
    assert data["person"]["name"] == "Ali"
