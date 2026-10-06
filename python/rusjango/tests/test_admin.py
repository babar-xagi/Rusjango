"""Admin permission boundaries, projections, bounded queries, and discovery."""

import sys
from types import ModuleType

import pytest

from rusjango import Field, Rusjango, Schema
from rusjango.admin import (
    AdminIdentity,
    AdminPermissionDenied,
    AdminReadOnlyError,
    AdminSite,
)
from rusjango.orm import (
    Boolean,
    DoesNotExist,
    Integer,
    Model,
    String,
    close_db,
    configure_db,
    init_db,
)
from rusjango.orm import connection, model as model_module
from rusjango.schema import SchemaValidationError
from conftest import call_asgi


class Person(Model):
    id = Integer(primary_key=True)
    name = String(max_length=100)
    age = Integer(nullable=True)
    active = Boolean(default=True)
    secret = String(default="not exposed")


class PersonCreate(Schema):
    name: str = Field(min_length=2, max_length=100)
    age: int | None = None


class PersonUpdate(Schema):
    name: str = Field(min_length=2, max_length=100)


def identity(*actions):
    return AdminIdentity(
        "staff", frozenset(f"admin:person:{action}" for action in actions)
    )


def site(**options):
    result = AdminSite()
    result.register(
        Person,
        list_display=("id", "name", "active"),
        detail_fields=("id", "name", "age", "active"),
        list_filter=("age", "active"),
        search_fields=("name",),
        **options,
    )
    return result


@pytest.fixture
async def database():
    previous = model_module._MODEL_REGISTRY[:]
    model_module._MODEL_REGISTRY[:] = [Person]
    await close_db()
    configure_db({"ENGINE": "sqlite", "NAME": ":memory:"})
    try:
        await init_db()
        yield
    finally:
        await close_db()
        configure_db(None)
        model_module._MODEL_REGISTRY[:] = previous


@pytest.mark.parametrize("actor", [None, "staff", True, AdminIdentity("staff")])
async def test_unauthorized_read_never_queries_database(actor, monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("No database access should occur")

    monkeypatch.setattr(connection, "fetchall", forbidden)
    with pytest.raises(AdminPermissionDenied):
        await site().list("person", identity=actor)


def test_catalog_is_filtered_and_default_model_is_readonly():
    registry = site()
    assert registry.catalog(identity=AdminIdentity("staff")) == []
    entry = registry.catalog(identity=identity("view", "add", "change", "delete"))[0]
    assert entry["capabilities"] == {"create": False, "update": False, "delete": False}
    assert "secret" not in str(entry)
    with pytest.raises(AdminPermissionDenied):
        registry.catalog()
    assert AdminSite().catalog(identity=identity("view")) == []


async def test_permission_cannot_enable_unconfigured_writes(database):
    registry = site()
    actor = identity("view", "add", "change", "delete")
    with pytest.raises(AdminReadOnlyError):
        await registry.create("person", {"name": "Sara"}, identity=actor)
    with pytest.raises(AdminReadOnlyError):
        await registry.update("person", 1, {"name": "Sara"}, identity=actor)
    with pytest.raises(AdminReadOnlyError):
        await registry.delete("person", 1, identity=actor)
    assert await Person.all() == []


async def test_projection_pagination_boolean_decode_and_stable_sort(database):
    for name in ["Zoe", "Ali", "Ali"]:
        await Person.create(name=name)
    registry = site()
    first = await registry.list(
        "person", identity=identity("view"), limit=2, sort="name"
    )
    assert [row["id"] for row in first["items"]] == [2, 3]
    assert first["has_more"] is True
    assert first["items"][0]["active"] is True
    assert "secret" not in str(first)
    last = await registry.list(
        "person", identity=identity("view"), limit=2, offset=2, sort="name"
    )
    assert [row["id"] for row in last["items"]] == [1]
    assert last["has_more"] is False
    detail = await registry.detail("person", 1, identity=identity("view"))
    assert set(detail) == {"id", "name", "age", "active"}


async def test_literal_search_and_null_range_filters(database):
    await Person.create(name="100%_done", age=22)
    await Person.create(name="100xyzdone", age=30)
    await Person.create(name="Null age")
    registry = site()
    result = await registry.list(
        "person", identity=identity("view"), search="%_", filters={"age__gte": 18}
    )
    assert [row["name"] for row in result["items"]] == ["100%_done"]
    assert (
        len(
            (
                await registry.list(
                    "person", identity=identity("view"), filters={"age": None}
                )
            )["items"]
        )
        == 1
    )
    assert (
        await registry.list("person", identity=identity("view"), search="' OR 1=1 --")
    )["items"] == []


@pytest.mark.parametrize(
    "options",
    [
        {"limit": True},
        {"limit": 101},
        {"offset": -1},
        {"offset": 10001},
        {"sort": "secret"},
        {"sort": False},
        {"sort": "name; DROP TABLE person"},
        {"filters": {"secret": "x"}},
        {"filters": {"age__in": [22]}},
        {"search": "x" * 257},
    ],
)
async def test_invalid_query_inputs_rejected_before_sql(options, monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Invalid inputs must not reach SQL")

    monkeypatch.setattr(connection, "fetchall", forbidden)
    configure_db({"ENGINE": "sqlite", "NAME": ":memory:"})
    try:
        with pytest.raises((ValueError, TypeError)):
            await site().list("person", identity=identity("view"), **options)
    finally:
        configure_db(None)


async def test_explicit_write_schemas_and_permissions(database):
    registry = site(
        create_schema=PersonCreate, update_schema=PersonUpdate, allow_delete=True
    )
    actor = identity("view", "add", "change", "delete")
    created = await registry.create("person", {"name": "Sara"}, identity=actor)
    assert created["name"] == "Sara" and "secret" not in created
    with pytest.raises(AdminPermissionDenied):
        await registry.update(
            "person", created["id"], {"name": "Ali"}, identity=identity("view")
        )
    for data in [
        {"id": 50, "name": "Ali"},
        {"secret": "leak", "name": "Ali"},
        {"name": "X"},
    ]:
        with pytest.raises(SchemaValidationError):
            await registry.update("person", created["id"], data, identity=actor)
    updated = await registry.update(
        "person", created["id"], {"name": "Ali"}, identity=actor
    )
    assert updated["name"] == "Ali"
    assert await registry.delete("person", created["id"], identity=actor) == 1
    with pytest.raises(DoesNotExist):
        await registry.detail("person", created["id"], identity=actor)


async def test_add_without_view_cannot_write_then_read(database):
    registry = site(create_schema=PersonCreate)
    with pytest.raises(AdminPermissionDenied):
        await registry.create("person", {"name": "Sara"}, identity=identity("add"))
    assert await Person.all() == []


def test_registration_checks_allowlists_schema_types_and_duplicates():
    registry = site()
    with pytest.raises(ValueError):
        registry.register(Person, list_display=("id", "name"))
    with pytest.raises(ValueError):
        AdminSite().register(Person, list_display=("name",))
    with pytest.raises(ValueError):
        AdminSite().register(Person, list_display=("id", "no_such_field"))

    class Wrong(Schema):
        name: int

    with pytest.raises(ValueError, match="does not match"):
        site(create_schema=Wrong)

    class Id(Schema):
        id: int
        name: str

    with pytest.raises(ValueError, match="Primary keys"):
        site(create_schema=Id)


def test_form_metadata_omits_default_values():
    class WriteOnly(Schema):
        name: str
        secret: str = Field(default="private default", min_length=3)

    registry = site(create_schema=WriteOnly)
    entry = registry.catalog(identity=identity("view", "add"))[0]
    assert "private default" not in str(entry)
    assert entry["create_form"][1]["constraints"] == {"min_length": 3}


def test_discovery_is_per_site_idempotent_and_rolls_back(monkeypatch):
    module = ModuleType("example.admin")
    calls = []

    def register(registry):
        calls.append(registry)
        registry.register(Person, list_display=("id", "name"))

    module.register = register
    monkeypatch.setitem(sys.modules, "example.admin", module)
    first, second = AdminSite(), AdminSite()
    first.autodiscover(["example"])
    first.autodiscover(["example"])
    second.autodiscover(["example"])
    assert calls == [first, second]
    broken = ModuleType("broken.admin")

    def fail(registry):
        registry.register(Person, list_display=("id", "name"))
        raise RuntimeError("registration failed")

    broken.register = fail
    monkeypatch.setitem(sys.modules, "broken.admin", broken)
    registry = AdminSite()
    with pytest.raises(RuntimeError):
        registry.autodiscover(["broken"])
    assert registry.catalog(identity=identity("view")) == []


def test_missing_dependency_in_admin_module_is_not_swallowed(monkeypatch):
    import importlib

    def missing(name):
        raise ModuleNotFoundError("dependency missing", name="missing_dependency")

    monkeypatch.setattr(importlib, "import_module", missing)
    with pytest.raises(ModuleNotFoundError):
        AdminSite().autodiscover(["example"])


async def test_app_loads_independent_factories_and_mounts_no_admin_routes(monkeypatch):
    module = ModuleType("admin_config")

    def factory(app):
        return site()

    module.create_site = factory
    monkeypatch.setitem(sys.modules, "admin_config", module)
    first, second = Rusjango(), Rusjango()
    for app in (first, second):
        app.settings["ADMIN"] = {"FACTORY": "admin_config:create_site"}
        app.load_installed_apps()
    assert first.admin_site is not second.admin_site
    assert first.load_admin() is first.admin_site
    assert (await call_asgi(first, path="/admin"))[0] == 404
    assert first.route_count == 0
    first.settings["ADMIN"] = None
    first.load_installed_apps()
    assert first.admin_site is None


def test_async_discovery_and_factory_are_rejected(monkeypatch):
    module = ModuleType("async_admin")

    async def create_site(app):
        return AdminSite()

    async def register(site):
        return None

    module.create_site = create_site
    monkeypatch.setitem(sys.modules, "async_admin", module)
    module2 = ModuleType("example.admin")
    module2.register = register
    monkeypatch.setitem(sys.modules, "example.admin", module2)
    app = Rusjango()
    app.settings["ADMIN"] = {"FACTORY": "async_admin:create_site"}
    with pytest.raises(TypeError, match="synchronous"):
        app.load_admin()
    with pytest.raises(TypeError, match="synchronous"):
        AdminSite().autodiscover(["example"])
