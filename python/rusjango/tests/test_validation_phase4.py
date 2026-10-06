"""Validation behavior, transformations, and HTTP failure locations."""

from typing import ClassVar

import pytest

from rusjango import Field, Rusjango, Schema, field_validator
from rusjango.schema import SchemaValidationError
from conftest import call_asgi


class Signup(Schema):
    __coerce__ = True
    label: str = Field(min_length=2, max_length=10, pattern=r"[A-Za-z ]+")
    age: int = Field(ge=18, le=100)
    enabled: bool = True
    weights: list[float] = []

    @field_validator("label")
    def trim_label(value):
        return value.strip()


class Interval(Schema):
    start: int
    end: int

    def validate(self):
        if self.end < self.start:
            raise ValueError("end must not precede start")


def test_coercion_and_validator_transform_preserve_declared_types():
    value = Signup(label=" Sara ", age="22", enabled="false", weights=["2.5", 3])
    assert value.dict() == {
        "label": "Sara",
        "age": 22,
        "enabled": False,
        "weights": [2.5, 3.0],
    }


@pytest.mark.parametrize("value", [True, 2.5, "2.5", {}, None])
def test_coercion_refuses_lossy_or_unrelated_integer_input(value):
    with pytest.raises(SchemaValidationError):
        Signup(label="Sara", age=value)


@pytest.mark.parametrize(
    "kwargs,field",
    [
        ({"label": "X", "age": 22}, "label"),
        ({"label": "Sara1", "age": 22}, "label"),
        ({"label": "Sara", "age": 17}, "age"),
        ({"label": "Sara", "age": 101}, "age"),
        ({"label": "  ", "age": 22}, "label"),
    ],
)
def test_constraints_apply_after_validator_transformation(kwargs, field):
    with pytest.raises(SchemaValidationError) as error:
        Signup(**kwargs)
    assert error.value.errors[0]["loc"] == [field]


def test_required_fields_and_independent_field_defaults():
    class Collection(Schema):
        items: list[int] = Field(default=[])
        count: int = Field(ge=0)

    with pytest.raises(SchemaValidationError):
        Collection()
    first, second = Collection(count=0), Collection(count=0)
    first.items.append(1)
    assert second.items == []


def test_union_prefers_an_exact_type_before_coercing():
    class Value(Schema):
        __coerce__ = True
        data: int | str

    assert Value(data="42").data == "42"


def test_nested_schema_controls_its_own_coercion_and_preserves_error_location():
    class Parent(Schema):
        __coerce__ = True
        child: Interval | None = None

    # Avoid unresolved function-local forward annotations.
    with pytest.raises(SchemaValidationError) as error:
        Parent(child={"start": "1", "end": 2})
    assert error.value.errors[0]["loc"] == ["child", "start"]


def test_validator_inheritance_and_explicit_override():
    class Base(Schema):
        internal: ClassVar[str] = "hidden"
        name: str

        @field_validator("name")
        def trim(value):
            return value.strip()

    class Child(Base):
        @field_validator("name")
        def trim(value):
            return value.upper()

    assert Base(name=" a ").dict() == {"name": "a"}
    assert Child(name=" b ").dict() == {"name": " B "}


def test_validator_output_is_type_checked_and_bad_configuration_is_not_a_client_error():
    class Broken(Schema):
        __coerce__ = True
        age: int

        @field_validator("age")
        def broken(value):
            return str(value)

    with pytest.raises(SchemaValidationError):
        Broken(age="22")
    with pytest.raises(TypeError):

        @field_validator("name")
        async def asynchronous(value):
            return value


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "nan", "inf"])
def test_non_finite_float_rejected(value):
    with pytest.raises(SchemaValidationError):
        Signup(label="Sara", age=22, weights=[value])


async def test_cross_field_validation_returns_body_location():
    app = Rusjango()

    @app.post("/")
    async def create(data: Interval):
        return data.dict()

    status, response = await call_asgi(app, method="POST", body=b'{"start":3,"end":2}')
    assert status == 422
    assert response["detail"] == [
        {"loc": ["body", "data"], "msg": "end must not precede start"}
    ]


async def test_http_constraints_and_coercion_apply_before_handler():
    app = Rusjango()

    @app.post("/")
    async def create(data: Signup):
        return data.dict()

    status, value = await call_asgi(
        app, method="POST", body=b'{"label":"Sara","age":"22"}'
    )
    assert status == 200 and value["age"] == 22
    status, response = await call_asgi(
        app, method="POST", body=b'{"label":"Sara","age":"17"}'
    )
    assert status == 422 and response["detail"][0]["loc"] == ["body", "data", "age"]


def test_coercion_cannot_silently_collapse_dictionary_keys():
    class Mapping(Schema):
        __coerce__ = True
        data: dict[int, str]

    with pytest.raises(SchemaValidationError, match="duplicate dictionary key"):
        Mapping(data={"1": "first", "01": "second"})


def test_float_overflow_is_a_validation_error():
    with pytest.raises(SchemaValidationError, match="finite"):
        Signup(label="Sara", age=22, weights=[10**1000])


def test_oversized_integer_string_is_a_validation_error():
    with pytest.raises(SchemaValidationError):
        Signup(label="Sara", age="9" * 5000)


def test_numeric_union_keeps_exact_integer_before_float_promotion():
    class Numeric(Schema):
        data: float | int

    assert type(Numeric(data=42).data) is int
