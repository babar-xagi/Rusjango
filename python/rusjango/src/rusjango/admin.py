"""Permission-gated admin foundations for trusted server-side callers.

No HTTP routes are installed. Authentication adapters and browser UI are separate.
"""

from __future__ import annotations

import importlib
import inspect
import re
from dataclasses import dataclass
from types import UnionType
from typing import get_args, get_origin, Union

from rusjango.orm import DoesNotExist, Integer, Model
from rusjango.orm import connection, sql
from rusjango.schema import Field as SchemaField
from rusjango.schema import Schema, SchemaValidationError, _MISSING, validate_value


class AdminPermissionDenied(PermissionError):
    """The caller has not supplied a trusted identity with the required grant."""


class AdminReadOnlyError(ValueError):
    """The model does not enable this write operation."""


@dataclass(frozen=True)
class AdminIdentity:
    """Trusted identity supplied by server code; this is not authentication."""

    subject: str
    permissions: frozenset[str] = frozenset()

    def __post_init__(self):
        if not isinstance(self.subject, str) or not self.subject.strip():
            raise ValueError("AdminIdentity requires a nonempty subject")
        if isinstance(self.permissions, str):
            raise TypeError("permissions must be a collection of strings")
        grants = frozenset(self.permissions)
        if not all(isinstance(grant, str) for grant in grants):
            raise TypeError("permissions must contain strings")
        object.__setattr__(self, "permissions", grants)


def _names(value, name, available, *, required=False):
    if not isinstance(value, (list, tuple)) or (required and not value):
        raise ValueError(f"{name} must be an explicit list or tuple of fields")
    result = tuple(value)
    if not all(isinstance(item, str) and item in available for item in result):
        raise ValueError(f"Unknown or unexposed field in {name}")
    if len(set(result)) != len(result):
        raise ValueError(f"Duplicate field in {name}")
    return result


def _label(model):
    parts = model.__module__.split(".")
    prefix = parts[1] + "." if len(parts) > 1 and parts[0] == "apps" else ""
    return prefix + model.__name__.lower()


@dataclass(frozen=True)
class ModelAdmin:
    model: type[Model]
    list_display: tuple[str, ...]
    label: str | None = None
    title: str | None = None
    detail_fields: tuple[str, ...] | None = None
    list_filter: tuple[str, ...] = ()
    search_fields: tuple[str, ...] = ()
    sortable_fields: tuple[str, ...] | None = None
    editable_fields: tuple[str, ...] | None = None
    create_schema: type[Schema] | None = None
    update_schema: type[Schema] | None = None
    allow_delete: bool = False
    page_size: int = 25

    def __post_init__(self):
        model = self.model
        if (
            not isinstance(model, type)
            or not issubclass(model, Model)
            or model is Model
            or model.__dict__.get("_abstract")
        ):
            raise TypeError("Register a concrete ORM Model")
        keys = [name for name, field in model._fields.items() if field.primary_key]
        if len(keys) != 1:
            raise ValueError("Admin models require one declared primary key")
        label = self.label or _label(model)
        if (
            not isinstance(label, str)
            or re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*", label) is None
        ):
            raise ValueError("Admin label must use lowercase identifier segments")
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "title", self.title or model.__name__)
        if not isinstance(self.title, str):
            raise TypeError("Admin title must be a string")
        if type(self.page_size) is not int or not 1 <= self.page_size <= 100:
            raise ValueError("page_size must be between 1 and 100")
        if type(self.allow_delete) is not bool:
            raise TypeError("allow_delete must be bool")
        fields = model._fields
        display = _names(self.list_display, "list_display", fields, required=True)
        details = _names(
            self.detail_fields if self.detail_fields is not None else display,
            "detail_fields",
            fields,
            required=True,
        )
        if keys[0] not in display or keys[0] not in details:
            raise ValueError(
                "Include the primary key in list_display and detail_fields"
            )
        for name, value in (
            ("list_display", display),
            ("detail_fields", details),
            ("list_filter", _names(self.list_filter, "list_filter", details)),
            ("search_fields", _names(self.search_fields, "search_fields", details)),
            (
                "sortable_fields",
                _names(
                    self.sortable_fields
                    if self.sortable_fields is not None
                    else display,
                    "sortable_fields",
                    details,
                ),
            ),
        ):
            object.__setattr__(self, name, value)
        for name in self.search_fields:
            if fields[name].python_type() is not str:
                raise ValueError("Search fields must store strings")
        schema_fields = set()
        for schema in (self.create_schema, self.update_schema):
            if schema is not None:
                if not isinstance(schema, type) or not issubclass(schema, Schema):
                    raise TypeError("Admin write schemas must subclass Schema")
                schema_fields.update(schema._hints())
        editable = _names(
            self.editable_fields
            if self.editable_fields is not None
            else tuple(sorted(schema_fields)),
            "editable_fields",
            fields,
        )
        if keys[0] in editable:
            raise ValueError("Primary keys are read-only")
        object.__setattr__(self, "editable_fields", editable)
        for schema in (self.create_schema, self.update_schema):
            if schema is not None:
                if not schema._hints() or not set(schema._hints()) <= set(editable):
                    raise ValueError(
                        "Write schema fields must be nonempty and editable"
                    )
                for name, annotation in schema._hints().items():
                    alternatives = (
                        get_args(annotation)
                        if get_origin(annotation) in (Union, UnionType)
                        else (annotation,)
                    )
                    expected = fields[name].python_type()
                    if any(
                        candidate is not expected and candidate is not type(None)
                        for candidate in alternatives
                    ):
                        raise ValueError(
                            f"Write schema type does not match ORM field: {name}"
                        )
                    if type(None) in alternatives and not fields[name].nullable:
                        raise ValueError(
                            f"Nonnullable ORM field cannot accept None: {name}"
                        )
        if self.create_schema is not None:
            if not isinstance(fields[keys[0]], Integer):
                raise ValueError(
                    "Admin creation currently requires a generated integer primary key"
                )
            required = {
                name
                for name, field in fields.items()
                if not field.primary_key
                and not field.nullable
                and field.default is None
            }
            if not required <= set(self.create_schema._hints()):
                raise ValueError("Create schema must include required ORM fields")

    @property
    def primary_key(self):
        return next(
            name for name, field in self.model._fields.items() if field.primary_key
        )

    def project(self, row, columns):
        return {
            name: bool(row[name])
            if row[name] is not None and self.model._fields[name].python_type() is bool
            else row[name]
            for name in columns
        }

    def payload(self, data, schema):
        if not isinstance(data, dict) or not all(isinstance(key, str) for key in data):
            raise SchemaValidationError(
                [], "Expected an object with string field names"
            )
        unknown = set(data) - set(schema._hints())
        if unknown:
            raise SchemaValidationError([sorted(unknown)[0]], "Field is not editable")
        return schema.from_dict(data).dict()

    def form(self, schema):
        if schema is None:
            return []
        result = []
        for name, hint in schema._hints().items():
            default = getattr(schema, name, _MISSING)
            required = (
                default is _MISSING
                or isinstance(default, SchemaField)
                and default.default is _MISSING
            )
            item = {
                "name": name,
                "type": self.model._fields[name].python_type().__name__,
                "nullable": self.model._fields[name].nullable,
                "required": required,
            }
            if isinstance(default, SchemaField):
                item["constraints"] = {
                    key: getattr(default, key)
                    for key in (
                        "ge",
                        "gt",
                        "le",
                        "lt",
                        "min_length",
                        "max_length",
                        "pattern",
                    )
                    if getattr(default, key) is not None
                }
            result.append(item)
        return result


class AdminSite:
    """Independent registry with permission-gated metadata and data services."""

    def __init__(self):
        self._registry: dict[str, ModelAdmin] = {}
        self._discovered: set[str] = set()
        self._discovering: set[str] = set()

    def register(self, model, **options) -> ModelAdmin:
        config = ModelAdmin(model=model, **options)
        if config.label in self._registry or any(
            entry.model is model for entry in self._registry.values()
        ):
            raise ValueError("Admin model or label already registered")
        self._registry[config.label] = config
        return config

    def autodiscover(self, installed_apps):
        for dotted in installed_apps:
            if not isinstance(dotted, str) or not dotted:
                raise TypeError("Installed admin apps must be dotted package names")
            name = dotted + ".admin"
            if name in self._discovered:
                continue
            if name in self._discovering:
                raise RuntimeError("Recursive admin discovery")
            snapshot = dict(self._registry)
            discovered = set(self._discovered)
            self._discovering.add(name)
            try:
                try:
                    module = importlib.import_module(name)
                except ModuleNotFoundError as exc:
                    if exc.name == name:
                        continue
                    raise
                callback = getattr(module, "register", None)
                if not callable(callback):
                    raise TypeError(f"{name} must define register(site)")
                if inspect.iscoroutinefunction(callback):
                    raise TypeError("Admin registration must be synchronous")
                result = callback(self)
                if inspect.isawaitable(result):
                    if inspect.iscoroutine(result):
                        result.close()
                    raise TypeError("Admin registration must be synchronous")
                self._discovered.add(name)
            except BaseException:
                self._registry = snapshot
                self._discovered = discovered
                raise
            finally:
                self._discovering.remove(name)

    @staticmethod
    def _identity(identity):
        if not isinstance(identity, AdminIdentity):
            raise AdminPermissionDenied("A trusted AdminIdentity is required")

    def _config(self, label, action, identity):
        self._identity(identity)
        if f"admin:{label}:{action}" not in identity.permissions:
            raise AdminPermissionDenied("Admin permission denied")
        if label not in self._registry:
            raise KeyError("Admin model is not registered")
        return self._registry[label]

    def catalog(self, *, identity=None):
        self._identity(identity)
        result = []
        for label, config in sorted(self._registry.items()):
            if f"admin:{label}:view" not in identity.permissions:
                continue
            result.append(
                {
                    "label": label,
                    "title": config.title,
                    "primary_key": config.primary_key,
                    "list_display": list(config.list_display),
                    "detail_fields": list(config.detail_fields),
                    "list_filter": list(config.list_filter),
                    "search_fields": list(config.search_fields),
                    "sortable_fields": list(config.sortable_fields),
                    "page_size": config.page_size,
                    "capabilities": {
                        "create": config.create_schema is not None
                        and f"admin:{label}:add" in identity.permissions,
                        "update": config.update_schema is not None
                        and f"admin:{label}:change" in identity.permissions,
                        "delete": config.allow_delete
                        and f"admin:{label}:delete" in identity.permissions,
                    },
                    "create_form": config.form(config.create_schema)
                    if f"admin:{label}:add" in identity.permissions
                    else [],
                    "update_form": config.form(config.update_schema)
                    if f"admin:{label}:change" in identity.permissions
                    else [],
                }
            )
        return result

    async def list(
        self,
        label,
        *,
        identity=None,
        limit=None,
        offset=0,
        sort=None,
        filters=None,
        search="",
    ):
        config = self._config(label, "view", identity)
        limit = config.page_size if limit is None else limit
        if (
            type(limit) is not int
            or not 1 <= limit <= 100
            or type(offset) is not int
            or not 0 <= offset <= 10000
        ):
            raise ValueError("Use limit 1..100 and offset 0..10000")
        if not isinstance(search, str) or len(search) > 256:
            raise ValueError("Search must be a string of at most 256 characters")
        if not isinstance(filters if filters is not None else {}, dict):
            raise TypeError("Filters must be a dictionary")
        checked = {}
        for lookup, value in (filters or {}).items():
            if not isinstance(lookup, str):
                raise ValueError("Invalid filter")
            name, _, operation = lookup.rpartition("__")
            name, operation = (name, operation) if name else (lookup, "exact")
            if name not in config.list_filter or operation not in (
                "exact",
                "gte",
                "gt",
                "lte",
                "lt",
            ):
                raise ValueError("Filter field or lookup is not allowed")
            field = config.model._fields[name]
            if value is None:
                if operation != "exact" or not field.nullable:
                    raise SchemaValidationError([name], "Null filter is not allowed")
            else:
                value = validate_value(value, field.python_type(), [name])
            checked[lookup] = value
        engine = connection.engine_name()
        where, params = sql.build_where(checked, engine)
        if search:
            if not config.search_fields:
                raise ValueError("Search is not configured")
            escaped = (
                search.lower()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            parts = []
            for name in config.search_fields:
                params.append("%" + escaped + "%")
                placeholder = "?" if engine == "sqlite" else "$" + str(len(params))
                parts.append(
                    f"LOWER({sql.quote_ident(name, engine)}) LIKE {placeholder} ESCAPE '\\'"
                )
            search_where = "(" + " OR ".join(parts) + ")"
            where = where + " AND " + search_where if where else search_where
        ordering = config.primary_key if sort is None else sort
        if not isinstance(ordering, str):
            raise ValueError("Sort must be a field name")
        descending = ordering.startswith("-")
        column = ordering[1:] if descending else ordering
        if column not in config.sortable_fields and column != config.primary_key:
            raise ValueError("Sort field is not allowed")
        order = sql.quote_ident(column, engine) + (" DESC" if descending else " ASC")
        if column != config.primary_key:
            order += ", " + sql.quote_ident(config.primary_key, engine) + " ASC"
        columns = ", ".join(
            sql.quote_ident(name, engine) for name in config.list_display
        )
        query = f"SELECT {columns} FROM {sql.quote_ident(config.model._table, engine)}"
        if where:
            query += " WHERE " + where
        query += f" ORDER BY {order} LIMIT {limit + 1} OFFSET {offset}"
        rows = await connection.fetchall(query, params)
        return {
            "model": label,
            "items": [config.project(row, config.list_display) for row in rows[:limit]],
            "columns": list(config.list_display),
            "limit": limit,
            "offset": offset,
            "has_more": len(rows) > limit,
        }

    async def detail(self, label, key, *, identity=None):
        config = self._config(label, "view", identity)
        return await self._detail(config, key)

    async def _detail(self, config, key):
        key = validate_value(
            key,
            config.model._fields[config.primary_key].python_type(),
            [config.primary_key],
        )
        where, params = sql.build_where(
            {config.primary_key: key}, connection.engine_name()
        )
        query, values = sql.select_sql(
            config.model._table, list(config.detail_fields), where, params, limit=1
        )
        row = await connection.fetchone(query, values)
        if row is None:
            raise DoesNotExist("Admin record does not exist")
        return config.project(row, config.detail_fields)

    async def create(self, label, data, *, identity=None):
        config = self._config(label, "add", identity)
        if config.create_schema is None:
            raise AdminReadOnlyError("Admin creation is disabled")
        # Returning visible data additionally requires read access.
        self._config(label, "view", identity)
        instance = await config.model.create(
            **config.payload(data, config.create_schema)
        )
        return config.project(instance.to_dict(), config.detail_fields)

    async def update(self, label, key, data, *, identity=None):
        config = self._config(label, "change", identity)
        if config.update_schema is None:
            raise AdminReadOnlyError("Admin updates are disabled")
        self._config(label, "view", identity)
        key = validate_value(
            key,
            config.model._fields[config.primary_key].python_type(),
            [config.primary_key],
        )
        payload = config.payload(data, config.update_schema)
        count = await config.model.filter(**{config.primary_key: key}).update(**payload)
        if not count:
            raise DoesNotExist("Admin record does not exist")
        return await self._detail(config, key)

    async def delete(self, label, key, *, identity=None):
        config = self._config(label, "delete", identity)
        if not config.allow_delete:
            raise AdminReadOnlyError("Admin deletion is disabled")
        key = validate_value(
            key,
            config.model._fields[config.primary_key].python_type(),
            [config.primary_key],
        )
        count = await config.model.filter(**{config.primary_key: key}).delete()
        if not count:
            raise DoesNotExist("Admin record does not exist")
        return count
