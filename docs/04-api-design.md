# API guide

Applies to Rusjango 0.1.4 (alpha).

```python
from rusjango import Rusjango, Router, Schema, HTTPException

app = Rusjango(settings='settings.py')

@app.get('/items/{id}')
async def item(id: int, limit: int = 10):
    return {'id': id, 'limit': limit}
```

GET, POST, PUT, and DELETE decorators accept a path. Literal characters are escaped; `{name}` captures one path segment. Path and query strings convert to str/int/float/bool. Boolean values accept true/false, yes/no, on/off, and 1/0. Invalid values and missing required inputs produce 422.

## Bodies

```python
class ItemCreate(Schema):
    name: str
    quantity: int = 1

@app.post('/items')
async def create(data: ItemCreate, limit: int = 10):
    return data.dict()
```

POST/PUT bodies are buffered and parsed as JSON. A Schema or plain dict body parameter receives the object; a query parameter cannot override it. Multiple independent Schema body parameters are not a supported API contract. Plain dict bodies must be JSON objects. Schema field validation is strict; [details](08-schema-validation.md).

## Responses

Dicts, lists, and other JSON-serializable values return 200. None returns 204 with an empty body. Raise HTTPException for another status:

```python
raise HTTPException(404, detail='Item not found')
```

Errors contain `error`, `status`, and optional `detail`. A known path with a different registered method returns 405 with Allow. An unknown path returns 404. Unexpected handler failures return 500; DEBUG adds the traceback under `detail`.

## App routers

Create `router = Router()` inside every app's api.py. `app.load_installed_apps()` mounts these under `/api/<app>/`. Avoid the exported singleton router in multi-app projects. Manual mounting uses `app.include_router(router, prefix='/api/items')`.

Routes match in registration order. No automatic HEAD/OPTIONS routes, request-object injection, dependency injection, streaming responses, file uploads, OpenAPI generation, or supported WebSockets exist yet.
