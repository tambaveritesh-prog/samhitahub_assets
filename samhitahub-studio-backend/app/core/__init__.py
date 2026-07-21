"""
Core package.

Houses cross-cutting, application-wide concerns that every other layer
depends on but that do not themselves depend on any feature/domain code:

- `config.py`    -> environment-driven settings (Pydantic Settings)
- `logging.py`   -> structured logging configuration
- `exceptions.py`-> custom exception hierarchy + FastAPI exception handlers
- `dependencies.py` -> shared FastAPI dependency-injection providers

Nothing in `core` should import from `app.api`, `app.services`,
`app.repositories`, or `app.modules`. The dependency direction always
points *inward* toward `core`, never outward from it. This keeps core
reusable and prevents circular imports as the project grows.
"""
