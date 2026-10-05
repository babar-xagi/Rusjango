# ✅ Schemas and validation

**Rusjango 0.1.4 · Alpha**

A `Schema` describes the fields your API accepts using Python type annotations. Rusjango validates those fields before calling a handler.

## 📝 Declare your input

```python
from rusjango import Schema


class StudentCreate(Schema):
    name: str
    age: int | None = None
```

| Input | Result |
|---|---|
| `{"name": "Ali", "age": 20}` | Valid |
| `{"name": "Ali"}` | Valid; age becomes `None` |
| `{"name": "Ali", "age": null}` | Valid |
| `{"name": "Ali", "age": "20"}` | Invalid; age is a string |
| `{"age": 20}` | Invalid; name is required |

JSON `null` becomes Python `None`.

## 📥 Use a schema in a route

In your generated project's `main.py`, place this route before `app.load_installed_apps()`:

```python
@app.post("/students")
async def create_student(data: StudentCreate):
    return data.dict()
```

The handler receives a validated `StudentCreate` instance. Calling `.dict()` produces JSON-compatible field data.

> 💡 **Response schemas are explicit:** Use `StudentOut.from_dict(...).dict()` when you want to validate output. Return annotations do not automatically validate responses.

## 🎯 Required, optional, and defaulted fields

A type that permits `None` and a default value serve different purposes:

```python
class RequiredNullable(Schema):
    age: int | None


class OmittableAge(Schema):
    age: int | None = None
```

`RequiredNullable` requires an `age` key, whose value may be null. `OmittableAge` also lets the caller omit the key.

Other defaults work the same way:

```python
class ItemCreate(Schema):
    name: str
    quantity: int = 1
    tags: list[str] = []
```

Defaults are copied for each instance, so the tags list is not shared.

## 🧱 Nested objects and collections

```python
class Address(Schema):
    city: str


class Person(Schema):
    name: str
    address: Address
    tags: list[str] = []
    scores: dict[str, int] = {}
```

Example input:

```json
{
  "name": "Sara",
  "address": {"city": "Lahore"},
  "tags": ["python", "apis"],
  "scores": {"math": 95}
}
```

`address` becomes an `Address` instance. `.dict()` recursively converts schemas, lists, and dictionaries to plain data.

## 🧪 Validate outside an HTTP handler

```python
student = StudentCreate.from_dict({"name": "Ali"})
assert student.dict() == {"name": "Ali", "age": None}
```

Direct construction uses the same validation rules:

```python
student = StudentCreate(name="Ali", age=20)
```

Unknown object keys are ignored. Integers are accepted for `float` fields; a `bool` is not accepted as an `int`.

## 🚫 Understand a validation error

For `create_student(data: StudentCreate)`, sending a numeric name produces:

```json
{
  "error": "Unprocessable Entity",
  "detail": [
    {"loc": ["body", "data", "name"], "msg": "Expected str"}
  ],
  "status": 422
}
```

The `loc` array identifies the body parameter and field. List errors also include the item index. Validation reports the first failure.

Outside HTTP handling, invalid data raises `SchemaValidationError`, a `ValueError` subclass:

```python
from rusjango.schema import SchemaValidationError

try:
    StudentCreate.from_dict({"name": 123})
except SchemaValidationError as exc:
    print(exc.errors)
```

## 📋 Supported types

| Type | Supported |
|---|---|
| `str`, `int`, `float`, `bool`, `None`, `Any` | Yes |
| Unions, including `int | None` | Yes |
| Other `Schema` subclasses | Yes |
| Typed lists and dictionaries | Yes |
| Field validators and numeric/length constraints | Pending |
| Literal, enums, dates, arbitrary generic containers | Pending |
| Automatic JSON Schema/OpenAPI generation | Pending |

Use strict JSON types today. Expanded validation remains part of Phase 4.

---

[← Routes and requests](04-api-design.md) · [📚 Documentation home](README.md) · [Next: Applications →](13-applications.md)
