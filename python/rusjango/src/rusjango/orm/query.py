"""QuerySet and filter lookups."""

from __future__ import annotations

from typing import Any, Generic, TypeVar, TYPE_CHECKING

from rusjango.orm import connection
from rusjango.orm import sql as sqlgen

if TYPE_CHECKING:
    from rusjango.orm.model import Model

M = TypeVar("M", bound="Model")


class DoesNotExist(Exception):
    pass


class MultipleObjectsReturned(Exception):
    pass


class QuerySet(Generic[M]):
    """Filterable async queryset."""

    def __init__(
        self, model_cls: type[M], filters: dict[str, Any] | None = None
    ) -> None:
        self._model_cls = model_cls
        self._filters = dict(filters or {})
        for lookup in self._filters:
            field = lookup.rsplit("__", 1)[0]
            if field not in model_cls._fields:
                raise ValueError(f"Unknown field: {field}")

    def filter(self, **kwargs: Any) -> QuerySet[M]:
        return QuerySet(self._model_cls, {**self._filters, **kwargs})

    async def _fetch(self, limit: int | None = None) -> list[M]:
        where, params = sqlgen.build_where(self._filters, connection.engine_name())
        columns = list(self._model_cls._fields.keys())
        query, query_params = sqlgen.select_sql(
            self._model_cls._table,
            columns,
            where,
            params,
            limit=limit,
        )
        rows = await connection.fetchall(query, tuple(query_params))
        return [self._model_cls._from_row(row) for row in rows]

    async def all(self) -> list[M]:
        return await self._fetch()

    async def first(self) -> M | None:
        rows = await self._fetch(limit=1)
        return rows[0] if rows else None

    async def get(self, **kwargs: Any) -> M:
        qs = self.filter(**kwargs) if kwargs else self
        rows = await qs._fetch(limit=2)
        if not rows:
            raise DoesNotExist(
                f"{self._model_cls.__name__} matching query does not exist."
            )
        if len(rows) > 1:
            raise MultipleObjectsReturned(
                f"get() returned more than one {self._model_cls.__name__}."
            )
        return rows[0]

    async def update(self, **values: Any) -> int:
        unknown = values.keys() - self._model_cls._fields.keys()
        if unknown:
            raise ValueError(f"Unknown fields: {', '.join(sorted(unknown))}")
        where, params = sqlgen.build_where(self._filters, connection.engine_name())
        if not where:
            msg = "update() requires at least one filter"
            raise ValueError(msg)
        query, query_params = sqlgen.update_sql(
            self._model_cls._table, values, where, params
        )
        return await connection.execute(query, tuple(query_params))

    async def delete(self) -> int:
        where, params = sqlgen.build_where(self._filters, connection.engine_name())
        if not where:
            msg = "delete() requires at least one filter"
            raise ValueError(msg)
        query, query_params = sqlgen.delete_sql(self._model_cls._table, where, params)
        return await connection.execute(query, tuple(query_params))
