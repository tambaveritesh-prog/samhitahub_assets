"""
Utils package.

Small, stateless, dependency-free helper functions used across the
codebase (date/time helpers, string/slug helpers, file helpers, etc.).

Rule: a function belongs here only if it has NO knowledge of FastAPI,
settings, services, or repositories — it should be pure and trivially
unit-testable in isolation. Anything that needs configuration or talks
to the outside world belongs in `services` or a `modules/*` package
instead.
"""
