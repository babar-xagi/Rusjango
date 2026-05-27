"""HTTP exceptions and error responses."""

from __future__ import annotations

from typing import Any


class HTTPException(Exception):
    """Raise to return an HTTP error response."""

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}
        super().__init__(detail)


def error_envelope(
    status_code: int,
    error: str,
    *,
    detail: Any = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    if detail is not None:
        body["detail"] = detail
    body["status"] = status_code
    return body
