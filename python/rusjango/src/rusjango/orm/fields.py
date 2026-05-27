"""ORM field types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Field:
    """Base model field."""

    primary_key: bool = False
    nullable: bool = False
    unique: bool = False
    default: Any = None
    name: str = ""

    def sql_type(self, engine: str) -> str:
        raise NotImplementedError

    def python_type(self) -> type:
        raise NotImplementedError


@dataclass
class Integer(Field):
    def sql_type(self, engine: str) -> str:
        if engine == "postgresql":
            return "INTEGER"
        return "INTEGER"

    def python_type(self) -> type:
        return int


@dataclass
class String(Field):
    max_length: int = 255

    def sql_type(self, engine: str) -> str:
        if engine == "postgresql":
            return f"VARCHAR({self.max_length})"
        return f"VARCHAR({self.max_length})"

    def python_type(self) -> type:
        return str


@dataclass
class Text(Field):
    def sql_type(self, engine: str) -> str:
        return "TEXT"

    def python_type(self) -> type:
        return str


@dataclass
class Boolean(Field):
    def sql_type(self, engine: str) -> str:
        if engine == "postgresql":
            return "BOOLEAN"
        return "INTEGER"

    def python_type(self) -> type:
        return bool
