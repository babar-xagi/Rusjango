"""Check lifespan and response framing through a real local Uvicorn server."""

from __future__ import annotations

import asyncio
import socket

import uvicorn

from rusjango import Rusjango


async def test_uvicorn_lifespan_and_empty_204():
    app = Rusjango()

    @app.delete("/")
    async def remove():
        return None

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, lifespan="on", log_level="error"))
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        async with asyncio.timeout(10):
            while not server.started:
                if task.done():
                    await task
                    raise AssertionError("Uvicorn stopped before startup")
                await asyncio.sleep(0.01)
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(
                b"DELETE / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
            )
            await writer.drain()
            response = await reader.read()
            writer.close()
            await writer.wait_closed()
        headers, body = response.split(b"\r\n\r\n", 1)
        assert headers.startswith(b"HTTP/1.1 204")
        assert body == b""
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=10)
        sock.close()
