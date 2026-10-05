"""Small, strict request/response schemas using Python type annotations."""

from __future__ import annotations

from copy import deepcopy
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints


class SchemaValidationError(ValueError):
    """An invalid field with a location suitable for an HTTP 422 response."""

    def __init__(self, location: list[str | int], message: str) -> None:
        self.errors = [{"loc": location, "msg": message}]
        super().__init__(message)


def validate_value(value: Any, annotation: Any, location: list[str | int]) -> Any:
    if annotation is Any:
        return value
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in (Union, UnionType):
        for candidate in args:
            try:
                return validate_value(value, candidate, location)
            except SchemaValidationError:
                pass
        raise SchemaValidationError(location, "Value does not match any allowed type")
    if isinstance(annotation, type) and issubclass(annotation, Schema):
        if isinstance(value, annotation):
            return value
        try:
            return annotation.from_dict(value)
        except SchemaValidationError as exc:
            for error in exc.errors:
                error["loc"] = location + error["loc"]
            raise
    if origin is list:
        if not isinstance(value, list):
            raise SchemaValidationError(location, "Expected list")
        return [
            validate_value(item, args[0], [*location, i])
            for i, item in enumerate(value)
        ]
    if origin is dict:
        if not isinstance(value, dict):
            raise SchemaValidationError(location, "Expected object")
        return {
            validate_value(key, args[0], location): validate_value(
                item, args[1], [*location, key]
            )
            for key, item in value.items()
        }
    if annotation is float and type(value) in (int, float):
        return float(value)
    if isinstance(annotation, type) and type(value) is annotation:
        return value
    raise SchemaValidationError(
        location, f"Expected {getattr(annotation, '__name__', annotation)}"
    )


def _to_dict(value: Any) -> Any:
    if isinstance(value, Schema):
        return value.dict()
    if isinstance(value, list):
        return [_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_dict(item) for key, item in value.items()}
    return value


class Schema:
    """Validate declared fields, ignore extra keys, and honour class defaults."""

    def __init__(self, **kwargs: Any) -> None:
        hints = get_type_hints(self.__class__)
        for key, annotation in hints.items():
            if key in kwargs:
                value = kwargs[key]
            elif hasattr(self.__class__, key):
                value = deepcopy(getattr(self.__class__, key))
            else:
                raise SchemaValidationError([key], "Field is required")
            setattr(self, key, validate_value(value, annotation, [key]))

    def dict(self) -> dict[str, Any]:
        hints = get_type_hints(self.__class__)
        return {key: _to_dict(getattr(self, key)) for key in hints}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Schema:
        if not isinstance(data, dict):
            raise SchemaValidationError([], "Expected JSON object")
        return cls(**data)
