# Settings

Applies to Rusjango 0.1.4 (alpha).

Rusjango imports the selected Python settings file and collects public uppercase names. Python code in that file is executed, so use only trusted configuration files.

| Setting | Purpose |
|---|---|
| APP_NAME | Human-readable application name |
| DEBUG | Adds traceback detail to 500 responses; bypasses host validation |
| ALLOWED_HOSTS | Production host allowlist; empty/missing list denies all hosts with SecurityMiddleware |
| INSTALLED_APPS | Dotted packages with api.py and a router object |
| MIDDLEWARE | Dotted ASGI middleware classes; first entry runs first |
| DATABASE | None, SQLite config, or PostgreSQL config |
| SECRET_KEY | Reserved for future signing/auth features; currently unused by framework |
| AUTH / ADMIN / AI / WORKER / PAYMENTS | Reserved settings; no implemented feature behavior |

Generated settings use DEBUG=True and allow localhost/127.0.0.1. Production host patterns support exact names, `*`, and `.example.com` (base domain plus subdomains). Bracketed IPv6 hosts are parsed without their brackets; configure `::1` to allow loopback IPv6.

```toml
[tool.rusjango]
settings = 'settings.py'
app = 'main:app'
```

The CLI reads these project keys. DATABASE NAME is relative to the working directory; CLI operations run from the detected project root. ASYNC is informational: ORM operations are always async.

SQLite config uses ENGINE and NAME. PostgreSQL uses ENGINE=postgresql (postgres is an alias), URL or DSN, and optional MIN_SIZE/MAX_SIZE (1/10 defaults). The asyncpg dependency is optional.

CLI editing supports literal list/dictionary/None values. Dynamic settings can be used by the runtime but require manual editing rather than feature-management commands.
