"""Model base class and registry."""

from __future__ import annotations

from copy import copy
from typing import Any, ClassVar

from rusjango.orm import connection
from rusjango.orm import sql as sqlgen
from rusjango.orm.fields import Boolean, Field
from rusjango.orm.query import QuerySet

_MODEL_REGISTRY: list[type[Model]] = []


class ModelMeta(type):
    def __new__(
        mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> type:
        fields: dict[str, Field] = {}
        for base in bases:
            fields.update(
                {
                    key: copy(value)
                    for key, value in getattr(base, "_fields", {}).items()
                }
            )
        for key, value in list(namespace.items()):
            if isinstance(value, Field):
                value.name = key
                fields[key] = value
                namespace.pop(key, None)
        cls = super().__new__(mcs, name, bases, namespace)
        cls._fields = fields
        if not namespace.get("_table"):
            cls._table = _default_table_name(cls)
        if sum(field.primary_key for field in fields.values()) > 1:
            raise ValueError("Models support one primary key")
        if (
            name != "Model"
            and not namespace.get("_abstract", False)
            and cls not in _MODEL_REGISTRY
        ):
            _MODEL_REGISTRY.append(cls)
        return cls


def _default_table_name(cls: type) -> str:
    module = cls.__module__
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == "apps":
        return f"{parts[1]}_{cls.__name__.lower()}"
    return cls.__name__.lower()


class Model(metaclass=ModelMeta):
    """Django-inspired async model base."""

    _fields: ClassVar[dict[str, Field]]
    _table: ClassVar[str]

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        parts = ", ".join(f"{k}={getattr(self, k, None)!r}" for k in self._fields)
        return f"{self.__class__.__name__}({parts})"

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name, None) for name in self._fields}

    @classmethod
    def registry(cls) -> list[type[Model]]:
        return list(_MODEL_REGISTRY)

    @classmethod
    def _from_row(cls, row: dict[str, Any]) -> Model:
        data: dict[str, Any] = {}
        for name, field in cls._fields.items():
            val = row.get(name)
            if val is not None and isinstance(field, Boolean):
                val = bool(val)
            data[name] = val
        return cls(**data)

    @classmethod
    async def create_table(cls, *, if_not_exists: bool = True) -> None:
        ddl = sqlgen.create_table_sql(cls._table, cls._fields)
        if not if_not_exists:
            ddl = ddl.replace("IF NOT EXISTS ", "")
        await connection.execute(ddl)

    @classmethod
    def filter(cls, **kwargs: Any) -> QuerySet:
        return QuerySet(cls, kwargs)

    @classmethod
    async def all(cls) -> list[Model]:
        return await cls.filter().all()

    @classmethod
    async def get(cls, **kwargs: Any) -> Model:
        return await cls.filter(**kwargs).get()

    @classmethod
    async def create(cls, **kwargs: Any) -> Model:
        row_data: dict[str, Any] = {}
        unknown = kwargs.keys() - cls._fields.keys()
        if unknown:
            raise ValueError(f"Unknown fields: {', '.join(sorted(unknown))}")

        for name, field in cls._fields.items():
            if name in kwargs:
                row_data[name] = kwargs[name]
            elif field.default is not None:
                row_data[name] = (
                    field.default() if callable(field.default) else field.default
                )
            elif field.primary_key:
                continue
            elif field.nullable:
                continue
            else:
                msg = f"Missing required field: {name}"
                raise ValueError(msg)

        query, params = sqlgen.insert_sql(
            cls._table, row_data, returning=list(cls._fields)
        )
        row = await connection.insert(query, params)
        return cls._from_row(row)
