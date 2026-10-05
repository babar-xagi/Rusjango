# Middleware

Applies to Rusjango 0.1.4 (alpha).

Middleware wraps an ASGI application. The first entry in MIDDLEWARE sees the request first and the response last.

```python
MIDDLEWARE = [
    'rusjango.security.SecurityMiddleware',
    'myapp.middleware.LoggingMiddleware',
]
```

```python
class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        settings = scope.get('rusjango', {}).get('settings', {})
        if scope['type'] == 'http':
            print(scope['method'], scope['path'], settings.get('APP_NAME'))
        await self.app(scope, receive, send)
```

Settings are attached before invoking middleware. Wrap send to inspect or modify responses. Keep mutable middleware state safe for concurrent requests.

SecurityMiddleware validates Host when DEBUG=False and rejects missing/disallowed hosts with 400. It adds X-Content-Type-Options: nosniff and X-Frame-Options: DENY, including rejected-host and HTTP error responses. With DEBUG=True, host validation is skipped.

Rusjango handles lifespan outside the HTTP middleware stack. Startup acknowledges the protocol and configures the backend; shutdown closes the configured database. No tables are created during startup. Auth, CORS, CSRF, sessions, rate limiting, and HTTPS redirection are not built-in middleware features.
