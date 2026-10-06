"""Strict schemas, optional coercion, constraints, and synchronous validators."""

from __future__ import annotations

import inspect
import math
import re
from copy import deepcopy
from dataclasses import dataclass
from types import UnionType
from typing import Any, ClassVar, Union, get_args, get_origin, get_type_hints

_MISSING = object()


class SchemaValidationError(ValueError):
    """A validation failure with a location suitable for an HTTP 422 response."""

    def __init__(self, location: list[str | int], message: str) -> None:
        self.errors = [{"loc": location, "msg": message}]
        super().__init__(message)


@dataclass(frozen=True)
class Field:
    """Schema field default and numeric/length/regex constraints."""

    default: Any = _MISSING
    ge: float | None = None
    gt: float | None = None
    le: float | None = None
    lt: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None

    def __post_init__(self):
        for name in ("ge", "gt", "le", "lt"):
            value = getattr(self, name)
            if value is not None and (
                type(value) not in (int, float) or not math.isfinite(value)
            ):
                raise ValueError(f"{name} must be a finite number")
        for name in ("min_length", "max_length"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{name} must be a nonnegative integer")
        if (
            self.min_length is not None
            and self.max_length is not None
            and self.min_length > self.max_length
        ):
            raise ValueError("min_length must not exceed max_length")
        if self.pattern is not None:
            re.compile(self.pattern)

    def check(self, value: Any, location: list[str | int]) -> None:
        if value is None:
            return
        for name, compare in (
            ("ge", lambda a, b: a >= b),
            ("gt", lambda a, b: a > b),
            ("le", lambda a, b: a <= b),
            ("lt", lambda a, b: a < b),
        ):
            bound = getattr(self, name)
            if bound is not None:
                if type(value) not in (int, float):
                    raise TypeError(f"{name} requires a numeric field")
                if not compare(value, bound):
                    raise SchemaValidationError(
                        location, f"Value must satisfy {name} {bound}"
                    )
        for name, compare in (
            ("min_length", lambda a, b: a >= b),
            ("max_length", lambda a, b: a <= b),
        ):
            bound = getattr(self, name)
            if bound is not None:
                if not isinstance(value, (str, list, dict)):
                    raise TypeError(f"{name} requires a string, list, or dictionary")
                if not compare(len(value), bound):
                    raise SchemaValidationError(
                        location, f"Length must satisfy {name} {bound}"
                    )
        if self.pattern is not None:
            if not isinstance(value, str):
                raise TypeError("pattern requires a string field")
            if re.fullmatch(self.pattern, value) is None:
                raise SchemaValidationError(
                    location, "Value does not match the pattern"
                )


def field_validator(*fields: str):
    """Decorate a synchronous value -> value function; runs after type validation."""
    if not fields or not all(isinstance(name, str) and name for name in fields):
        raise TypeError("field_validator requires field names")

    def decorate(function):
        if not inspect.isfunction(function) or inspect.iscoroutinefunction(function):
            raise TypeError("field validators must be synchronous functions")
        function.__rusjango_fields__ = fields
        return staticmethod(function)

    return decorate


def _coerce(value: Any, annotation: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if annotation is int and re.fullmatch(r"[+-]?[0-9]+", text):
            try:
                return int(text)
            except ValueError:
                return value
        if annotation is float:
            try:
                return float(text)
            except ValueError:
                pass
        if annotation is bool:
            if text.lower() in ("true", "1", "yes", "on"):
                return True
            if text.lower() in ("false", "0", "no", "off"):
                return False
    return value


def validate_value(
    value: Any, annotation: Any, location: list[str | int], *, coerce: bool = False
) -> Any:
    if annotation is Any:
        return value
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, UnionType):
        errors = []
        # Exact types take priority regardless of union annotation order.
        exact_first = sorted(args, key=lambda candidate: type(value) is not candidate)
        for candidate in exact_first:
            try:
                return validate_value(value, candidate, location)
            except SchemaValidationError as exc:
                errors.append(exc)
        if coerce:
            for candidate in args:
                try:
                    return validate_value(value, candidate, location, coerce=True)
                except SchemaValidationError:
                    pass
        # Preserve useful locations inside a nested object/collection.
        detailed = next(
            (error for error in errors if len(error.errors[0]["loc"]) > len(location)),
            None,
        )
        if detailed is not None:
            raise detailed
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
            validate_value(
                item, args[0] if args else Any, [*location, i], coerce=coerce
            )
            for i, item in enumerate(value)
        ]
    if origin is dict:
        if not isinstance(value, dict):
            raise SchemaValidationError(location, "Expected object")
        key_type, value_type = args or (Any, Any)
        result = {}
        for key, item in value.items():
            converted = validate_value(key, key_type, location, coerce=coerce)
            if converted in result:
                raise SchemaValidationError(
                    [*location, key], "Coercion produces a duplicate dictionary key"
                )
            result[converted] = validate_value(
                item, value_type, [*location, key], coerce=coerce
            )
        return result
    if coerce:
        value = _coerce(value, annotation)
    if annotation is float and type(value) in (int, float):
        try:
            value = float(value)
        except OverflowError as exc:
            raise SchemaValidationError(location, "Expected a finite number") from exc
    if annotation is float and type(value) is float and not math.isfinite(value):
        raise SchemaValidationError(location, "Expected a finite number")
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
    """Validate declared fields, ignore extra keys, and honor class defaults."""

    __coerce__: ClassVar[bool] = False

    @classmethod
    def _hints(cls) -> dict[str, Any]:
        return {
            name: hint
            for name, hint in get_type_hints(cls).items()
            if not name.startswith("_") and get_origin(hint) is not ClassVar
        }

    def __init__(self, **kwargs: Any) -> None:
        if type(self.__coerce__) is not bool:
            raise TypeError("Schema.__coerce__ must be a bool")
        hints = self._hints()
        methods = {}
        for base in reversed(type(self).__mro__):
            methods.update(vars(base))
        validators: dict[str, list[Any]] = {name: [] for name in hints}
        for name, descriptor in methods.items():
            function = (
                descriptor.__func__
                if isinstance(descriptor, staticmethod)
                else descriptor
            )
            for field in getattr(function, "__rusjango_fields__", ()):
                if field not in hints:
                    raise TypeError(f"Validator references unknown field: {field}")
                validators[field].append(getattr(type(self), name))
        for key, annotation in hints.items():
            specification = getattr(type(self), key, _MISSING)
            field = (
                specification
                if isinstance(specification, Field)
                else Field(default=specification)
            )
            if key in kwargs:
                value = kwargs[key]
            elif field.default is not _MISSING:
                value = deepcopy(field.default)
            else:
                raise SchemaValidationError([key], "Field is required")
            value = validate_value(value, annotation, [key], coerce=self.__coerce__)
            for validator in validators[key]:
                try:
                    value = validator(value)
                except ValueError as exc:
                    raise SchemaValidationError([key], str(exc)) from exc
                if inspect.isawaitable(value):
                    if inspect.iscoroutine(value):
                        value.close()
                    raise TypeError("Field validators must return synchronous values")
                value = validate_value(value, annotation, [key])
            field.check(value, [key])
            setattr(self, key, value)
        if inspect.iscoroutinefunction(self.validate):
            raise TypeError("Schema.validate must be synchronous")
        try:
            result = self.validate()
        except ValueError as exc:
            raise SchemaValidationError([], str(exc)) from exc
        if result is not None:
            raise TypeError("Schema.validate must return None")

    def validate(self) -> None:
        """Override to check relationships between fully validated fields."""

    def dict(self) -> dict[str, Any]:
        return {key: _to_dict(getattr(self, key)) for key in self._hints()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Schema:
        if not isinstance(data, dict):
            raise SchemaValidationError([], "Expected JSON object")
        return cls(**data)
