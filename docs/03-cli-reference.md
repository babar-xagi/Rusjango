# CLI reference

Applies to Rusjango 0.1.4 (alpha).

Use `rusjango` after installing the Python package, `python -m rusjango`, or the compiled Rust binary. Run `--help` for options.

| Command | Behavior |
|---|---|
| `new <name> [-d DIR]` | Creates `DIR/<name>` with exactly three files; refuses an existing destination |
| `dev [--host HOST] [--port PORT] [--no-reload]` | Starts Uvicorn; reload enabled by default |
| `add app <name>` | Creates `apps/<name>`, registers it, and ensures route loading |
| `remove app <name> [--yes]` | Unregisters and deletes the app; prompts by default |
| `add orm` | Enables SQLite if disabled; adds missing models/schemas and upgrades untouched starter APIs |
| `remove orm [--yes]` | Sets DATABASE to None; preserves model/schema/API files and data |
| `migrate` | Creates missing model tables and propagates failure as a nonzero exit |

Project detection reads `[tool.rusjango]` in a parent `pyproject.toml`. Its settings path is respected. Standard scaffolds use `main.py` and `app` as the application object.

Project names accept letters, digits, `_`, and `-`. App names must be Python identifiers beginning with a letter or `_`; `apps` and `rusjango` are reserved. Removing a symlinked app is refused.

## Editing and preservation

Both CLIs support literal INSTALLED_APPS lists with single or double quotes. DATABASE must be None or a dictionary. Computed settings are not a supported editing format; edit them manually. The edited value may be normalized and comments inside that value removed; unrelated file contents are preserved.

`add orm` never replaces a custom API based merely on its imports. It upgrades only the exact untouched starter API. Existing model/schema files stay intact. Apps added after ORM activation also receive ORM starter files.

`remove orm` disables database access, not ORM-dependent routes. Adapt those handlers manually. `migrate` does not alter columns, rename tables, roll back changes, or track migration history.

Rust embeds templates, so an installed binary does not require the source checkout. Its dev/migrate commands require Python and prefer uv, with a Python fallback when uv is unavailable.

Auth, admin, Docker, tests, workers, AI, and payments commands are not implemented.
