# ✅ Schemas and validation

**Rusjango 0.1.5 · Alpha**

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

### 🎯 Field constraints

Use `Field` from `rusjango` for schema constraints. ORM fields remain separate classes in `rusjango.orm`.

```python
from rusjango import Field


class Order(Schema):
    title: str = Field(min_length=2, max_length=100)
    quantity: int = Field(default=1, ge=1, le=100)
    tags: list[str] = Field(default=[], max_length=10)
```

`ge`, `gt`, `le`, and `lt` constrain numeric values. `min_length` and `max_length` work on strings, lists, and dictionaries. `pattern` performs a full regex match on a string. Nullable values skip constraints when their annotation permits None.

`Field()` without a default is required. Field defaults are copied per instance.

### 🔄 Opt-in coercion and field validators

Strict validation stays the default. Enable controlled conversions on a schema explicitly:

```python
from rusjango import field_validator


class Signup(Schema):
    __coerce__ = True
    name: str = Field(min_length=2)
    age: int = Field(ge=18, le=120)

    @field_validator("name")
    def trim_name(value):
        return value.strip()


signup = Signup.from_dict({"name": " Ada ", "age": "22"})
assert signup.dict() == {"name": "Ada", "age": 22}
```

The decorator creates a static value-to-value function; do not add `self`, `cls`, or a classmethod decorator. A validator may transform its value or raise `ValueError` with a useful message. Its output is type-checked without coercion before Field constraints are checked.

Validators are inherited. Overriding a method by name replaces that inherited validator. Multiple field validators run in declaration/MRO order. Defaults run through the same checks.

| Target | Coercion with `__coerce__ = True` |
|---|---|
| `int` | Signed integer strings, with surrounding whitespace stripped |
| `float` | Numeric strings; result must be finite |
| `bool` | true/false, yes/no, on/off, 1/0 strings; case-insensitive |
| Lists/dictionaries | Apply that policy to their annotated elements |
| Nested Schema | Uses that nested class's own coercion setting |

Booleans and fractional numbers are never converted to integers. Values are not stringified into `str` fields. Unions prefer an exact match before trying conversions, so `int | str` keeps `"22"` as a string. Dictionary keys that collide after conversion are rejected.

Float fields reject NaN, infinity, and overflow even in strict mode. Private annotations and ClassVar metadata are not serialized fields.

### 🧱 Cross-field validation

Override `validate()` to check the fully validated object:

```python
class Interval(Schema):
    start: int
    end: int

    def validate(self):
        if self.end < self.start:
            raise ValueError("end must not precede start")
```

The hook is synchronous and returns None. A ValueError becomes a model-level validation failure; in a handler body its location identifies the body parameter. Field-validator failures identify the field.

Use ValueError for invalid input. Invalid validator configuration and programming errors are not converted into validation failures.

| Type | Supported |
|---|---|
| `str`, `int`, `float`, `bool`, `None`, `Any` | Yes |
| Unions, including `int | None` | Yes |
| Other `Schema` subclasses | Yes |
| Typed lists and dictionaries | Yes |
| Field validators, cross-field checks, and Field constraints | Yes |
| Literal, enums, dates, arbitrary generic containers | Pending |
| Automatic JSON Schema/OpenAPI generation | Pending |

Strict JSON types are the default. Coercion and validators are explicit extensions; generated JSON Schema/OpenAPI remains pending.

---

[← Routes and requests](04-api-design.md) · [📚 Documentation home](README.md) · [Next: Applications →](13-applications.md)
