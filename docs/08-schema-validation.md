# Schema validation

Applies to Rusjango 0.1.4 (alpha).

Schemas enforce declared types and required fields. They do not coerce JSON strings into numbers or booleans.

```python
from rusjango import Schema

class Address(Schema):
    city: str

class Person(Schema):
    name: str
    age: int | None = None
    address: Address | None = None
    tags: list[str] = []
```

Person.from_dict creates a validated object. Person(**kwargs) uses the same rules. dict() recursively serializes nested schemas and collections. Unknown keys are ignored. Defaults are copied per instance, so mutable defaults are not shared.

Supported annotations: str, int, float, bool, None, Any, unions/optional types, other Schema subclasses, lists, and dictionaries. Integers are accepted for float fields; bool is not accepted for an integer field. Optional type annotations allow null but do not make a field omittable unless a default is declared.

```python
person = Person.from_dict({'name': 'Ali', 'address': {'city': 'Lahore'}})
payload = person.dict()
```

Direct validation raises SchemaValidationError, a ValueError subclass exposing errors with loc and msg. Handler body validation converts it into an HTTP 422 response. Validation reports the first encountered failure rather than aggregating all invalid fields.

Current limits: no field validators, numeric/length constraints, Literal/enums/date types, arbitrary generic containers, Pydantic auto-parsing, JSON Schema generation, or OpenAPI. Full Phase 4 validation policy remains pending; strict supported types are the current contract.
