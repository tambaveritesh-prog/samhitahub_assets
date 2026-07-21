"""
API package.

Holds everything related to HTTP transport: routers and endpoint
handlers. This layer should be thin — it parses/validates requests
(mostly automatic via Pydantic schemas), calls into the `services`
layer to do the actual work, and shapes the response. Business logic
does NOT belong here.

Sub-packages are organized by API version (`v1`, and later `v2`, ...)
so that breaking changes can be introduced in a new version without
disturbing existing clients (the Android apps).
"""
