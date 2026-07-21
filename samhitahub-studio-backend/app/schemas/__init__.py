"""
Schemas package.

Pydantic models that define the HTTP request/response contract of the
API (the `api` layer's request bodies, query/path params where
non-trivial, and response bodies). These are what shows up in the
OpenAPI docs at `/docs`.

See `app/models/__init__.py` for the distinction between `models` and
`schemas`.
"""
