"""
Shared pytest fixtures.

`client` builds a fresh app (via `create_app`) per test using
`Settings(environment=Environment.TEST, ...)`, then wraps it in an
async HTTP client so endpoint tests can make real requests against it
without a running server process.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Environment, Settings
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        environment=Environment.TEST,
        debug=True,
        log_json=False,
    )


@pytest_asyncio.fixture
async def client(test_settings: Settings) -> AsyncIterator[AsyncClient]:
    app = create_app(settings=test_settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
