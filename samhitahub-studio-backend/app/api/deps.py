"""
API-layer dependencies.

Distinct from `app.core.dependencies`: providers here are specific to
handling HTTP requests (e.g. extracting/validating an auth token from
headers) rather than generic app-wide concerns.

This file is currently a placeholder. When authentication is
implemented, add something like:

    async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        settings: SettingsDep,
    ) -> User:
        ...

and expose it as `CurrentUserDep = Annotated[User, Depends(get_current_user)]`
for reuse across endpoint modules.
"""

from __future__ import annotations

# Intentionally empty for now — see module docstring.
