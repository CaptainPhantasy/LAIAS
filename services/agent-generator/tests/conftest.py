"""
Pytest configuration for Agent Generator tests.
"""

import os
import sys

import pytest

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Enable dev mode auth for tests (so routes don't require JWT)
os.environ.setdefault("AUTH_DEV_MODE", "true")


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return {
        "openai_api_key": "test-key",
        "anthropic_api_key": "test-key",
        "database_url": "sqlite:///:memory:",
        "redis_url": "redis://localhost:6379/1",
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test")
