"""Async database connections (SQLite and PostgreSQL)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

_db_config: dict[str, Any] | None = None
_sqlite_conn: Any = None
_pg_pool: Any = None


def configure_db(config: dict[str, Any] | None) -> None:
    global _db_config
    _db_config = config


def get_db_config() -> dict[str, Any]:
    if not _db_config:
        msg = "DATABASE is not configured. Run `rusjango add orm` first."
        raise RuntimeError(msg)
    return _db_config


def engine_name() -> str:
    return str(get_db_config().get("ENGINE", "sqlite")).lower()


@asynccontextmanager
async def acquire() -> AsyncIterator[Any]:
    """Yield a DB connection (aiosqlite Connection or asyncpg Connection)."""
    eng = engine_name()
    if eng == "sqlite":
        conn = await _sqlite_connection()
        try:
            yield conn
        finally:
            pass
    elif eng in ("postgresql", "postgres"):
        conn = await _pg_acquire()
        try:
            yield conn
        finally:
            if hasattr(conn, "release"):
                await conn.release()
    else:
        msg = f"Unsupported DATABASE ENGINE: {eng}"
        raise RuntimeError(msg)


async def _sqlite_connection() -> Any:
    global _sqlite_conn
    if _sqlite_conn is not None:
        return _sqlite_conn
    import aiosqlite

    cfg = get_db_config()
    path = cfg.get("NAME") or cfg.get("URL", "db.sqlite3")
    if isinstance(path, str) and path.startswith("sqlite"):
        path = "db.sqlite3"
    _sqlite_conn = await aiosqlite.connect(path)
    _sqlite_conn.row_factory = aiosqlite.Row
    return _sqlite_conn


async def _pg_acquire() -> Any:
    pool = await _pg_pool_get()
    return await pool.acquire()


async def _pg_pool_get() -> Any:
    global _pg_pool
    if _pg_pool is not None:
        return _pg_pool
    import asyncpg

    cfg = get_db_config()
    dsn = cfg.get("URL") or cfg.get("DSN")
    if not dsn:
        msg = "PostgreSQL DATABASE requires URL or DSN"
        raise RuntimeError(msg)
    _pg_pool = await asyncpg.create_pool(dsn)
    return _pg_pool


async def execute(sql: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
    eng = engine_name()
    async with acquire() as conn:
        if eng == "sqlite":
            await conn.execute(sql, params)
            await conn.commit()
        else:
            await conn.execute(sql, *params)


async def fetchall(sql: str, params: tuple[Any, ...] | list[Any] = ()) -> list[dict[str, Any]]:
    eng = engine_name()
    async with acquire() as conn:
        if eng == "sqlite":
            cursor = await conn.execute(sql, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        rows = await conn.fetch(sql, *params)
        return [dict(row) for row in rows]


async def fetchone(sql: str, params: tuple[Any, ...] | list[Any] = ()) -> dict[str, Any] | None:
    rows = await fetchall(sql, params)
    return rows[0] if rows else None


async def init_db() -> None:
    """Create tables for all registered models."""
    from rusjango.orm.model import Model

    for model_cls in Model.registry():
        await model_cls.create_table(if_not_exists=True)


async def close_db() -> None:
    global _sqlite_conn, _pg_pool
    if _sqlite_conn is not None:
        await _sqlite_conn.close()
        _sqlite_conn = None
    if _pg_pool is not None:
        await _pg_pool.close()
        _pg_pool = None
