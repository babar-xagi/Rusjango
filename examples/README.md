# 🧪 School API example

**Rusjango 0.1.5 · Alpha**

The bundled example shows an app router, strict schemas, and SQLite CRUD using the workspace package.

## ▶️ Run it

From the repository root in WSL2:

```bash
uv sync --all-packages --all-extras
cd examples/hello
uv run rusjango migrate
uv run rusjango dev
```

## 📥 Create a student

```bash
curl -X POST http://127.0.0.1:8000/api/school/students \
  -H "Content-Type: application/json" -d '{"name":"Ali"}'
```

The response includes a generated integer ID and `"age": null`.

## 📤 List students

```bash
curl http://127.0.0.1:8000/api/school/students
```

## ✅ Check validation

Send `"age": "20"` instead of an integer to receive a 422 response.

Run `migrate` before database requests; startup does not create tables. Stop the server with Ctrl+C.

> 💡 **Environment:** This example uses the source workspace. Keep Windows and WSL virtual environments separate.

---

[📚 Documentation](../docs/README.md) · [First steps](../docs/02-getting-started.md) · [ORM guide](../docs/05-orm-guide.md)
