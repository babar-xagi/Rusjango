# 🌐 Routes and requests

**Rusjango 0.1.4 · Alpha**

A route connects an HTTP method and URL path to an async Python function. This guide builds on the generated project from [First steps](02-getting-started.md).

## 🟢 A GET route

Add routes above `app.load_installed_apps()` in `main.py`:

```python
@app.get("/health")
async def health():
    return {"ok": True}
```

Request:

```bash
curl http://127.0.0.1:8000/health
```

Response:

```json
{"ok": true}
```

Dicts, lists, and JSON-compatible values return **200**.

## 🛤️ Path parameters

A name inside braces captures one path segment:

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

| Request | Result |
|---|---|
| `GET /items/7` | `{"item_id": 7}` |
| `GET /items/hello` | 422: invalid integer |

Literal path characters are matched literally. Register specific routes before overlapping parameter routes; routes match in registration order.

## 🔎 Query parameters

Arguments that are not path parameters can come from the query string:

```python
@app.get("/search")
async def search(term: str, limit: int = 10, active: bool = True):
    return {"term": term, "limit": limit, "active": active}
```

```bash
curl "http://127.0.0.1:8000/search?term=python&limit=5&active=false"
```

```json
{"term": "python", "limit": 5, "active": false}
```

| Annotation | Accepted URL values |
|---|---|
| `str` | Text |
| `int` | Integer strings such as `"5"` |
| `float` | Numeric strings such as `"2.5"` |
| `bool` | true/false, yes/no, on/off, 1/0; case-insensitive |

A missing required query argument returns 422. An argument with a default uses that default when omitted. Repeated query keys use the final value.

> 💡 **URL conversion and JSON validation differ:** Query strings are converted from text. JSON schema fields are validated as typed values; an integer field does not accept a JSON string.

## 📥 JSON request bodies

Declare a schema and use it as a handler argument:

```python
from rusjango import Schema


class ItemCreate(Schema):
    name: str
    quantity: int = 1


@app.post("/items")
async def create_item(data: ItemCreate):
    return data.dict()
```

```bash
curl -X POST http://127.0.0.1:8000/items \
  -H "Content-Type: application/json" -d '{"name":"Notebook"}'
```

```json
{"name": "Notebook", "quantity": 1}
```

POST and PUT bodies are buffered and parsed as JSON. Invalid JSON and invalid schema fields return 422. A single Schema or plain `dict` argument can receive the body; a query key with that argument's name cannot replace it.

Use one Schema body parameter per handler. The framework does not define a multiple-Schema body contract.

Learn defaults, nested objects, and supported types in the [schema guide](08-schema-validation.md).

## ✏️ PUT and DELETE

```python
@app.put("/items/{item_id}")
async def replace_item(item_id: int, data: ItemCreate):
    return {"id": item_id, **data.dict()}


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return None
```

Returning `None` sends **204 No Content** with an empty body.

These examples demonstrate request handling. Persisting changes requires ORM calls or another storage layer.

## 🚫 Return an HTTP error

Use `HTTPException` for an intentional error response:

```python
from rusjango import HTTPException


@app.get("/missing")
async def missing():
    raise HTTPException(404, detail="Item not found")
```

```json
{"error": "Not Found", "detail": "Item not found", "status": 404}
```

| Situation | Status |
|---|---|
| Unknown path | 404 |
| Known path with a different registered method | 405, with an `Allow` header |
| Invalid JSON, invalid parameter, or missing required input | 422 |
| Unexpected handler failure | 500 |
| Handler returns `None` | 204 |

With `DEBUG = True`, unexpected handler errors include traceback detail. Disable debug when running outside development.

## 🧭 Current boundaries

There are GET, POST, PUT, and DELETE decorators. Automatic HEAD/OPTIONS routes, request-object injection, dependencies, uploads, streaming, WebSockets, and generated OpenAPI/Swagger pages are not implemented.

---

[← First steps](02-getting-started.md) · [📚 Documentation home](README.md) · [Next: Schemas →](08-schema-validation.md)
