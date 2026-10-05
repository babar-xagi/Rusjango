# Python runtime internals

Applies to Rusjango 0.1.4 (alpha).

Rusjango is the main ASGI callable; Router is an alias used to create isolated app route tables. The exported singleton router remains a single-file convenience.

## Dispatch

__call__ attaches settings before middleware. HTTP requests traverse the lazily cached stack. Lifespan startup/shutdown is handled directly; unsupported WebSocket connections are closed. Only the documented HTTP and lifecycle behavior is supported.

routing.py compiles escaped literal path segments with named parameter captures. Routes match in registration order. call_handler resolves path/query parameters, then body data, validates supported annotations, checks required parameters, and awaits the handler. Signature/type-hint inspection currently occurs per request.

asgi.py buffers request chunks, parses JSON, and sends JSON/error envelopes. No request-size limit or streaming response API exists. None handler results produce empty 204 responses. Serialization still uses json.dumps(default=str).

## Apps and settings

load_settings executes a trusted Python settings file and extracts uppercase names. Settings belong to the application instance and are placed on scope. Database config/connections and the model registry remain process-wide.

load_installed_apps imports `<package>.api`, mounts its router under `/api/<leaf>`, and imports models when a database is configured. Already mounted packages are tracked to avoid duplicate routes. Missing model modules may be skipped, but missing dependencies inside those modules propagate.

The Python CLI uses AST locations and literal evaluation for settings edits; it does not execute settings to mutate them. Unrelated file contents are preserved, while edited-value formatting/comments may change.
