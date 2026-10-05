"""Async database connections (SQLite and PostgreSQL)."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

_db_config: dict[str, Any] | None = None
_sqlite_conn: Any = None
_pg_pool: Any = None
_sqlite_lock: asyncio.Lock | None = None
_pg_init_lock: asyncio.Lock | None = None


def configure_db(config: dict[str, Any] | None) -> None:
    global _db_config, _sqlite_lock, _pg_init_lock
    if (_sqlite_conn is not None or _pg_pool is not None) and config != _db_config:
        raise RuntimeError("Close the current database before changing DATABASE")
    if _sqlite_conn is None and _pg_pool is None and config != _db_config:
        _sqlite_lock = None
        _pg_init_lock = None
    _db_config = dict(config) if config else None


def get_db_config() -> dict[str, Any]:
    if not _db_config:
        msg = "DATABASE is not configured. Run `rusjango add orm` first."
        raise RuntimeError(msg)
    return _db_config


def engine_name() -> str:
    engine = str(get_db_config().get("ENGINE", "sqlite")).lower()
    return "postgresql" if engine == "postgres" else engine


@asynccontextmanager
async def acquire() -> AsyncIterator[Any]:
    """Yield a DB connection (aiosqlite Connection or asyncpg Connection)."""
    eng = engine_name()
    if eng == "sqlite":
        global _sqlite_lock
        if _sqlite_lock is None:
            _sqlite_lock = asyncio.Lock()
        async with _sqlite_lock:
            yield await _sqlite_connection()
    elif eng in ("postgresql", "postgres"):
        pool = await _pg_pool_get()
        conn = await pool.acquire()
        try:
            yield conn
        finally:
            await pool.release(conn)
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


async def _pg_pool_get() -> Any:
    global _pg_pool, _pg_init_lock
    if _pg_pool is not None:
        return _pg_pool
    import asyncpg

    cfg = get_db_config()
    dsn = cfg.get("URL") or cfg.get("DSN")
    if not dsn:
        msg = "PostgreSQL DATABASE requires URL or DSN"
        raise RuntimeError(msg)
    if _pg_init_lock is None:
        _pg_init_lock = asyncio.Lock()
    async with _pg_init_lock:
        if _pg_pool is None:
            _pg_pool = await asyncpg.create_pool(
                dsn,
                min_size=cfg.get("MIN_SIZE", 1),
                max_size=cfg.get("MAX_SIZE", 10),
            )
    return _pg_pool


async def execute(sql: str, params: tuple[Any, ...] | list[Any] = ()) -> int:
    eng = engine_name()
    async with acquire() as conn:
        if eng == "sqlite":
            try:
                async with conn.execute(sql, params) as cursor:
                    count = max(cursor.rowcount, 0)
                await conn.commit()
                return count
            except BaseException:
                await conn.rollback()
                raise
        else:
            status = await conn.execute(sql, *params)
            count = status.rsplit(" ", 1)[-1]
            return int(count) if count.isdigit() else 0


async def insert(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any]:
    """Read INSERT ... RETURNING on the same connection as the insert."""
    eng = engine_name()
    async with acquire() as conn:
        if eng == "sqlite":
            try:
                async with conn.execute(sql, params) as cursor:
                    row = await cursor.fetchone()
                await conn.commit()
            except BaseException:
                await conn.rollback()
                raise
        else:
            row = await conn.fetchrow(sql, *params)
        if row is None:
            raise RuntimeError("INSERT did not return a row")
        return dict(row)


async def fetchall(
    sql: str, params: tuple[Any, ...] | list[Any] = ()
) -> list[dict[str, Any]]:
    eng = engine_name()
    async with acquire() as conn:
        if eng == "sqlite":
            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        rows = await conn.fetch(sql, *params)
        return [dict(row) for row in rows]


async def fetchone(
    sql: str, params: tuple[Any, ...] | list[Any] = ()
) -> dict[str, Any] | None:
    async with acquire() as conn:
        if engine_name() == "sqlite":
            async with conn.execute(sql, params) as cursor:
                row = await cursor.fetchone()
        else:
            row = await conn.fetchrow(sql, *params)
        return dict(row) if row is not None else None


async def init_db() -> None:
    """Create tables for all registered models."""
    from rusjango.orm.model import Model

    for model_cls in Model.registry():
        await model_cls.create_table(if_not_exists=True)


async def close_db() -> None:
    global _sqlite_conn, _pg_pool, _sqlite_lock, _pg_init_lock
    if _sqlite_conn is not None:
        await _sqlite_conn.close()
        _sqlite_conn = None
    if _pg_pool is not None:
        await _pg_pool.close()
        _pg_pool = None
    _sqlite_lock = None
    _pg_init_lock = None
