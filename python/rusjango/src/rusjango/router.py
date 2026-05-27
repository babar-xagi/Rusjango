"""Per-app API router (used by generated apps/*/api.py).

NOTE: The module-level `router` is a shared singleton — only safe for single-app
projects. For multi-app projects, each api.py should create its own instance:

    from rusjango import Router
    router = Router()
"""

from __future__ import annotations

from rusjango.app import Rusjango

# Global singleton — convenient for tiny single-file projects.
# Multi-app projects: use `from rusjango import Router; router = Router()` instead.
router = Rusjango()

get = router.get
post = router.post
put = router.put
delete = router.delete

__all__ = ["router", "get", "post", "put", "delete"]
