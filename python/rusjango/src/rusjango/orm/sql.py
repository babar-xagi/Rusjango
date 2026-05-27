"""SQL generation helpers."""

from __future__ import annotations

from typing import Any

from rusjango.orm.connection import engine_name
from rusjango.orm.fields import Boolean, Field


def quote_ident(name: str, engine: str) -> str:
    if engine in ("postgresql", "postgres"):
        return f'"{name}"'
    return f'"{name}"'


def column_def(field: Field, engine: str) -> str:
    parts = [quote_ident(field.name, engine), field.sql_type(engine)]
    if field.primary_key:
        parts.append("PRIMARY KEY")
        if engine == "sqlite":
            parts = [quote_ident(field.name, engine), "INTEGER PRIMARY KEY AUTOINCREMENT"]
    if not field.nullable and not field.primary_key:
        parts.append("NOT NULL")
    if field.unique and not field.primary_key:
        parts.append("UNIQUE")
    return " ".join(parts)


def create_table_sql(table: str, fields: dict[str, Field]) -> str:
    engine = engine_name()
    cols = ", ".join(column_def(f, engine) for f in fields.values())
    return f"CREATE TABLE IF NOT EXISTS {quote_ident(table, engine)} ({cols})"


def insert_sql(table: str, data: dict[str, Any]) -> tuple[str, tuple[Any, ...]]:
    engine = engine_name()
    keys = list(data.keys())
    cols = ", ".join(quote_ident(k, engine) for k in keys)
    placeholders = ", ".join("?" if engine == "sqlite" else f"${i+1}" for i in range(len(keys)))
    sql = f"INSERT INTO {quote_ident(table, engine)} ({cols}) VALUES ({placeholders})"
    return sql, tuple(_encode_value(data[k], engine) for k in keys)


def select_sql(
    table: str,
    columns: list[str],
    where: str,
    params: list[Any],
    limit: int | None = None,
) -> tuple[str, list[Any]]:
    engine = engine_name()
    cols = ", ".join(quote_ident(c, engine) for c in columns)
    sql = f"SELECT {cols} FROM {quote_ident(table, engine)}"
    if where:
        sql += f" WHERE {where}"
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    return sql, params


def update_sql(table: str, data: dict[str, Any], where: str, params: list[Any]) -> tuple[str, list[Any]]:
    engine = engine_name()
    sets = []
    values: list[Any] = []
    for i, (key, val) in enumerate(data.items(), start=1):
        if engine == "sqlite":
            sets.append(f"{quote_ident(key, engine)} = ?")
        else:
            sets.append(f"{quote_ident(key, engine)} = ${i}")
        values.append(_encode_value(val, engine))
    sql = f"UPDATE {quote_ident(table, engine)} SET {', '.join(sets)}"
    if where:
        sql += f" WHERE {where}"
    return sql, values + params


def delete_sql(table: str, where: str, params: list[Any]) -> tuple[str, list[Any]]:
    engine = engine_name()
    sql = f"DELETE FROM {quote_ident(table, engine)}"
    if where:
        sql += f" WHERE {where}"
    return sql, params


def build_where(filters: dict[str, Any], engine: str) -> tuple[str, list[Any]]:
    """Parse filters like age__gte=18 into SQL."""
    clauses: list[str] = []
    params: list[Any] = []
    idx = 1
    for key, value in filters.items():
        if "__" in key:
            field, op = key.rsplit("__", 1)
        else:
            field, op = key, "exact"
        col = quote_ident(field, engine)
        if op == "exact":
            if engine == "sqlite":
                clauses.append(f"{col} = ?")
            else:
                clauses.append(f"{col} = ${idx}")
                idx += 1
            params.append(_encode_value(value, engine))
        elif op == "gte":
            if engine == "sqlite":
                clauses.append(f"{col} >= ?")
            else:
                clauses.append(f"{col} >= ${idx}")
                idx += 1
            params.append(_encode_value(value, engine))
        elif op == "lte":
            if engine == "sqlite":
                clauses.append(f"{col} <= ?")
            else:
                clauses.append(f"{col} <= ${idx}")
                idx += 1
            params.append(_encode_value(value, engine))
        elif op == "gt":
            if engine == "sqlite":
                clauses.append(f"{col} > ?")
            else:
                clauses.append(f"{col} > ${idx}")
                idx += 1
            params.append(_encode_value(value, engine))
        elif op == "lt":
            if engine == "sqlite":
                clauses.append(f"{col} < ?")
            else:
                clauses.append(f"{col} < ${idx}")
                idx += 1
            params.append(_encode_value(value, engine))
        else:
            msg = f"Unsupported lookup: {key}"
            raise ValueError(msg)
    if not clauses:
        return "", []
    return " AND ".join(clauses), params


def _encode_value(value: Any, engine: str) -> Any:
    if isinstance(value, bool):
        return int(value) if engine == "sqlite" else value
    return value
