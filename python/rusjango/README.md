# Rusjango

**Rust-powered async Python web framework**

*Start like Flask · Scale like Django · Perform like Rust · Build AI apps natively*

[![PyPI](https://img.shields.io/pypi/v/rusjango)](https://pypi.org/project/rusjango/)
[![Python](https://img.shields.io/pypi/pyversions/rusjango)](https://pypi.org/project/rusjango/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/babar-xagi/Rusjango/blob/main/LICENSE)

---

## Install

```bash
uv add rusjango
# or
pip install rusjango

# PostgreSQL support
uv add rusjango[postgres]
```

## Quick start

```bash
rusjango new myapp
cd myapp
rusjango dev
```

Open http://127.0.0.1:8000

## What it looks like

```python
# main.py
from rusjango import Rusjango

app = Rusjango(settings="settings.py")

@app.get("/")
async def home():
    return {"message": "Hello Rusjango"}

@app.get("/items/{id}")
async def get_item(id: int):
    return {"id": id}
```

## Progressive growth

```bash
rusjango add app school       # adds apps/school/ with its own API router
rusjango add orm              # enables async ORM (SQLite default)
rusjango migrate              # creates database tables
rusjango add auth             # coming: JWT + sessions
rusjango add admin            # coming: modern React admin panel
rusjango remove app school    # safely removes any feature
```

## ORM

```python
from rusjango.orm import Model, Integer, String

class Student(Model):
    id   = Integer(primary_key=True)
    name = String(max_length=100)
    age  = Integer(nullable=True)

# CRUD
student = await Student.create(name="Ali", age=20)
students = await Student.filter(age__gte=18).all()
await Student.filter(id=1).update(name="Ahmed")
await Student.filter(id=1).delete()
```

## Per-app routing

```python
# apps/school/api.py
from rusjango import Router

router = Router()   # fresh instance per app — no route cross-contamination

@router.get("/students")
async def list_students():
    return [{"name": "Ali"}, {"name": "Sara"}]
```

Routes are auto-mounted at `/api/school/students`.

## Tech stack

| Layer | Technology |
|---|---|
| HTTP / ASGI | Python + uvicorn |
| CLI | Rust + clap |
| Rust extension | PyO3 + maturin |
| Database (SQLite) | aiosqlite |
| Database (PostgreSQL) | asyncpg |

---

**Full docs:** [github.com/babar-xagi/Rusjango/tree/main/docs](https://github.com/babar-xagi/Rusjango/tree/main/docs)

**Source:** [github.com/babar-xagi/Rusjango](https://github.com/babar-xagi/Rusjango)
