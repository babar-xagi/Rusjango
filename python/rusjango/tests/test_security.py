"""Host parsing and rejection responses through the actual middleware stack."""

from __future__ import annotations

import pytest

from rusjango import Rusjango
from test_regressions import exchange, http_scope


@pytest.mark.parametrize(
    "host,status",
    [
        ("example.com", 200),
        ("www.example.com:8000", 200),
        ("example.com.", 200),
        ("evil-example.com", 400),
        ("example.com@evil.com", 400),
        ("[example.com]evil", 400),
        ("example.com:bad", 400),
        ("example.com/path", 400),
        ("[::1]:8000", 200),
        ("[::1]evil", 400),
    ],
)
async def test_production_hosts(host, status):
    app = Rusjango()
    app.settings = {
        "DEBUG": False,
        "ALLOWED_HOSTS": [".example.com", "::1"],
        "MIDDLEWARE": ["rusjango.security.SecurityMiddleware"],
    }

    @app.get("/")
    async def home():
        return {}

    messages = await exchange(app, http_scope(host=host))
    assert messages[0]["status"] == status
    assert dict(messages[0]["headers"])[b"x-frame-options"] == b"DENY"


async def test_malformed_json_errors_keep_security_headers():
    app = Rusjango()
    app.settings = {
        "DEBUG": False,
        "ALLOWED_HOSTS": ["localhost"],
        "MIDDLEWARE": ["rusjango.security.SecurityMiddleware"],
    }

    @app.post("/")
    async def create(data: dict):
        return data

    messages = await exchange(
        app,
        http_scope(method="POST"),
        [
            {"type": "http.request", "body": b"\xff", "more_body": False},
        ],
    )
    assert messages[0]["status"] == 422
    assert dict(messages[0]["headers"])[b"x-frame-options"] == b"DENY"
