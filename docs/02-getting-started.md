# 🚀 First steps

**Rusjango 0.1.6 · Alpha**

In this tutorial, you will install Rusjango, create a project, start the server, and check your first JSON response.

## 📋 Requirements

- Python **3.11 or newer**.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for the recommended workflow.
- Rust only if you are building from source or working on the Rust CLI.

Published wheels cover Linux x86_64/aarch64, Windows x86_64, and macOS x86_64/arm64. A platform without a compatible wheel may need a Rust source build.

## 📦 Install and create a project

Use uv to run the CLI in an isolated tool environment:

```bash
uvx --from rusjango==0.1.6 rusjango new demo
cd demo
uv sync
```

`uv sync` installs the generated project's dependencies into its own `.venv`.

The initial scaffold has three files:

```text
demo/
├── main.py
├── settings.py
└── pyproject.toml
```

> 💡 **Use the project environment:** Once you are inside `demo`, run commands with `uv run rusjango`. This keeps the CLI and your application's dependencies in the same environment.

<a id="install-with-pip"></a>
### Install with pip

If you prefer pip, create and activate a virtual environment first.

**Linux, macOS, or WSL:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Then:

```bash
python -m pip install rusjango==0.1.6
python -m rusjango new demo
cd demo
python -m rusjango dev
```

Keep using that active environment for the pip workflow. Install any additional application dependencies into it. The commands below use uv; with pip, replace `uv run rusjango` with `python -m rusjango`.

## ▶️ Run the development server

Inside your project:

```bash
uv run rusjango dev
```

The server listens at **http://127.0.0.1:8000/** and reloads after code changes.

Open that URL or use:

```bash
curl http://127.0.0.1:8000/
```

Response:

```json
{"message": "Hello Rusjango"}
```

Stop the server with **Ctrl+C**.

## ✍️ Add your first route

The generated `main.py` creates the application with `settings.py` and loads installed apps. Add this route above `app.load_installed_apps()`:

```python
@app.get("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello {name}"}
```

Restart the server and open **http://127.0.0.1:8000/hello/Ali**.

```json
{"message": "Hello Ali"}
```

The `{name}` path segment becomes the handler's `name` argument.

## 🧩 Try the bundled example

From a source checkout:

```bash
git clone https://github.com/babar-xagi/Rusjango.git
cd Rusjango
uv sync --all-packages --all-extras
cargo build -p rusjango-cli

cd examples/hello
uv run rusjango migrate
uv run rusjango dev
```

Visit **http://127.0.0.1:8000/api/school/students**.

> 💡 **Database setup:** Run `migrate` before database-backed requests. Server startup does not create tables.

The repository pins Python 3.12. To use Python 3.14 in your WSL shell:

```bash
export UV_PYTHON=3.14
uv sync --all-packages --all-extras
```

Keep Windows and WSL virtual environments separate. For Cargo checks, point `PYO3_PYTHON` to the absolute `.venv/bin/python` path if system Python lacks its development library.

If your existing checkout is at `D:\Rusjango` on Windows, use `cd /mnt/d/Rusjango` inside WSL instead of cloning it again.

## 🔬 Use unreleased source in a new project

From the repository root:

```bash
uv run python -m rusjango new demo
uv venv demo/.venv
uv pip install --python demo/.venv/bin/python -e ./python/rusjango
cd demo
.venv/bin/python -m rusjango dev
```

This installs the checkout into the new project's environment. A normal generated-project `uv sync` uses the package index.

## 🛠️ Troubleshooting

| Symptom | Check |
|---|---|
| `No module named rusjango` | Use the environment where you installed the package |
| “No Rusjango project found” | Run from a directory beneath the project's `pyproject.toml` |
| Database table is missing | Stop the server, run `migrate`, then restart |
| Production requests return 400 | Check `ALLOWED_HOSTS` and the request's Host header |
| WSL cannot use a Windows venv | Create a Linux venv from inside WSL |

---

[← Overview](00-overview.md) · [📚 Documentation home](README.md) · [Next: Routes and requests →](04-api-design.md)
