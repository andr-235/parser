"""Pytest configuration and fixtures."""

import asyncio

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    """Create an async test client for FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_settings():
    """Test settings override."""
    return {
        "ENVIRONMENT": "test",
        "DEBUG": True,
        "SECRET_KEY": "test-secret-key-for-testing-purposes-only",
        "DATABASE_URL": "sqlite:///test.db",
        "REDIS_URL": "redis://localhost:6379/1",
        "VK_ACCESS_TOKEN": "test-token",
    }
