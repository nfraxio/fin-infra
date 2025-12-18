"""Pytest configuration for fin-infra acceptance tests.

This conftest automatically loads environment variables from .env file
to make acceptance tests work seamlessly with local development setup.
"""

import asyncio
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import httpx
import pytest


class _SyncASGIClient:
    """Synchronous wrapper around httpx.AsyncClient for acceptance tests."""

    def __init__(self, app) -> None:
        self._loop = asyncio.new_event_loop()
        self._client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            timeout=10.0,
        )

    def _run(self, coro):
        try:
            asyncio.set_event_loop(self._loop)
        except RuntimeError:
            pass
        return self._loop.run_until_complete(coro)

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return self._run(self._client.request(method, url, **kwargs))

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("PATCH", url, **kwargs)

    def close(self) -> None:
        self._run(self._client.aclose())
        self._loop.close()
        asyncio.set_event_loop(None)


@pytest.fixture(scope="session")
def client() -> Generator[httpx.Client, None, None]:
    """HTTPX client for acceptance scenarios.

    If ``BASE_URL`` is provided we target that network endpoint.
    Otherwise we run the acceptance app in-process via ``ASGITransport``.
    """
    base_url = os.getenv("BASE_URL")
    if base_url:
        with httpx.Client(base_url=base_url, timeout=10.0) as c:
            yield c
        return

    # In-process fallback: lazily import acceptance app
    from .app import make_app

    acceptance_app = make_app()

    try:
        prev_loop = asyncio.get_running_loop()
    except RuntimeError:
        prev_loop = None

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        # Run startup if app has router.startup
        if hasattr(acceptance_app, "router") and hasattr(acceptance_app.router, "startup"):
            loop.run_until_complete(acceptance_app.router.startup())

        client_wrapper = _SyncASGIClient(acceptance_app)
        try:
            yield client_wrapper
        finally:
            client_wrapper.close()
            # Run shutdown if app has router.shutdown
            if hasattr(acceptance_app, "router") and hasattr(acceptance_app.router, "shutdown"):
                loop.run_until_complete(acceptance_app.router.shutdown())
    finally:
        loop.close()
        asyncio.set_event_loop(prev_loop)


def pytest_configure(config):
    """Load .env file before running acceptance tests."""
    # Find .env file in project root
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"

    if env_file.exists():
        # Simple .env parser (no dependencies needed)
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                # Parse KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value
