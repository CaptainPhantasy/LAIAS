"""
Pytest configuration for Agent Generator tests.
"""

import pytest
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return {
        "openai_api_key": "test-key",
        "anthropic_api_key": "test-key",
        "database_url": "sqlite:///:memory:",
        "redis_url": "redis://localhost:6379/1"
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addiniption(
        "markers", "asyncio: mark test as async"
    )
    config.addiniption(
        "markers", "integration: mark test as integration test"
    )
