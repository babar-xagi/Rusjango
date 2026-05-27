# Schema and Validation

Rusjango ships a lightweight `Schema` class for defining request/response shapes using standard Python type hints. It is intentionally minimal — a pragmatic alternative to Pydantic for projects that don't need the full validation stack.

---

## What is Schema?

`Schema` provides:

- **Request body parsing** — populate a typed object from a JSON request body dict.
- **Response serialization** — convert a schema instance back to a plain dict for JSON responses.
- **Self-documenting signatures** — route handlers declare their inputs by type annotation, and Rusjango automatically resolves and instantiates the right schema.

It does **not** require any third-party libraries.

---

## Basic usage

```python
from rusjango import Schema


class StudentCreate(Schema):
    name: str
    age: int


class StudentOut(Schema):
    id: int
    name: str
    age: int
```

Fields are declared as class-level type-annotated attributes. The `Schema` metaclass (or `__init_subclass__`) collects them at class definition time.

---

## Schema methods

### `Schema.from_dict(data: dict) -> Schema`

Class method. Creates an instance by reading only the keys that are declared on the schema — extra keys in `data` are silently ignored.

```python
body = {"name": "Alice", "age": 20, "extra_field": "ignored"}
student = StudentCreate.from_dict(body)
# student.name == "Alice"
# student.age  == 20
```

### `instance.dict() -> dict`

Returns all declared fields and their current values as a plain `dict`.

```python
student = StudentCreate.from_dict({"name": "Alice", "age": 20})
student.dict()
# {"name": "Alice", "age": 20}
```

---

## Using schemas in route handlers

Rusjango inspects handler function signatures using `inspect.signature` and `typing.get_type_hints`. When a parameter's type is a `Schema` subclass, the framework:

1. Reads the raw request body.
2. Parses it as JSON.
3. Calls `MySchema.from_dict(parsed_body)`.
4. Passes the resulting instance as the parameter.

```python
from rusjango import Router, Schema

router = Router()


class StudentCreate(Schema):
    name: str
    age: int


class StudentOut(Schema):
    id: int
    name: str
    age: int


@router.post("/students")
async def create_student(data: StudentCreate) -> dict:
    # data.name and data.age are already available as typed attributes
    new_student = await Student.create(name=data.name, age=data.age)
    return StudentOut.from_dict(new_student.__dict__).dict()
```

The response is serialized to JSON automatically when the handler returns a `dict`.

### Combining path params and schema body

```python
@router.put("/students/{id}")
async def update_student(id: int, data: StudentCreate) -> dict:
    student = await Student.get(id=id)
    await student.update(name=data.name, age=data.age)
    return StudentOut.from_dict(student.__dict__).dict()
```

- `id` is resolved from the URL path (type-coerced to `int`).
- `data` is resolved from the request body.

---

## Parameter resolution order

When Rusjango resolves handler parameters, it checks in this order:

| Source | Condition |
|---|---|
| Path parameter | Name matches a `{param}` in the URL pattern |
| Query parameter | Name matches a `?key=value` in the query string |
| Schema body | Type annotation is a `Schema` subclass |
| ASGI scope | Type annotation is `dict` and name is `scope` *(reserved)* |

---

## Limitations (current phase)

The current `Schema` implementation is intentionally simple. Known limitations:

- **No automatic type coercion** — if a field is declared as `int` but the JSON sends `"20"` (a string), the value is stored as a string, not an integer. Type casting must be done manually.
- **No nested schema validation** — a field of type `Address` (another Schema subclass) is not recursively parsed.
- **No field validators** — there is no equivalent of Pydantic's `@field_validator`.
- **No optional fields with defaults** — all declared fields are required. A `name: str = "Anonymous"` default is not yet honoured at parse time.
- **No error details** — when a required field is missing, the error message does not currently indicate which field is absent.

---

## Planned improvements (Phase 4 / Phase 7)

| Feature | Target phase |
|---|---|
| Type coercion (`str` → `int`, `str` → `float`, etc.) | Phase 4 |
| Optional fields with defaults | Phase 4 |
| Nested schema validation | Phase 4 |
| Field-level validators (`@validator`) | Phase 4 |
| Detailed validation error responses (422 Unprocessable Entity) | Phase 4 |
| OpenAPI / JSON Schema generation | Phase 7 |
| Pydantic v2 compatibility layer | Phase 7 |

---

## Using Pydantic directly

Because Rusjango's handler resolution checks for `Schema` subclasses specifically, standard Pydantic models are **not** auto-parsed from the request body in the current phase. You can still use Pydantic manually:

```python
from pydantic import BaseModel

class StudentCreate(BaseModel):
    name: str
    age: int

@router.post("/students")
async def create_student(scope: dict, receive) -> dict:
    import json
    body = b""
    async for chunk in ...:   # read body manually
        body += chunk
    data = StudentCreate.model_validate_json(body)
    ...
```

Full Pydantic integration (automatic body parsing for `BaseModel` subclasses) is planned for Phase 4.
