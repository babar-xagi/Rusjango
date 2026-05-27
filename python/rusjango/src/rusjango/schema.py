"""Request/response schema helpers (validation-lite)."""

from __future__ import annotations

from typing import Any, get_type_hints


class Schema:
    """Simple data schema with dict conversion."""

    def __init__(self, **kwargs: Any) -> None:
        hints = get_type_hints(self.__class__)
        for key, value in kwargs.items():
            if key in hints:
                setattr(self, key, value)

    def dict(self) -> dict[str, Any]:
        hints = get_type_hints(self.__class__)
        return {key: getattr(self, key) for key in hints}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Schema:
        hints = get_type_hints(cls)
        filtered = {k: data[k] for k in hints if k in data}
        return cls(**filtered)
