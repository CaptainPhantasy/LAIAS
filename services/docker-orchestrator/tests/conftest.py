"""
Pytest configuration and fixtures.
"""

import os
import pytest
import docker
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def docker_client():
    """Docker client for testing."""
    return docker.from_env()


@pytest.fixture
def test_agent_code():
    """Sample agent code for testing."""
    return '''
async def flow(ctx: RunContext) -> Result:
    """Sample test flow."""
    await ctx.log("Test flow executing")
    return ctx.result(success=True, data={"test": True})
'''


@pytest.fixture
def test_agents_yaml():
    """Sample agents.yaml for testing."""
    return '''
version: "1.0"
agents:
  - name: test_agent
    role: Test agent for orchestrator
    instructions: You are a helpful test agent
'''


@pytest.fixture
def test_deployment_request(test_agent_code, test_agents_yaml):
    """Sample deployment request."""
    from app.models.requests import DeployAgentRequest

    return DeployAgentRequest(
        agent_id="test-agent-001",
        agent_name="Test Agent",
        flow_code=test_agent_code,
        agents_yaml=test_agents_yaml,
        requirements=["pydantic>=2.0"],
        cpu_limit=0.5,
        memory_limit="256m",
        auto_start=False,  # Don't auto-start in tests
    )


@pytest.fixture(autouse=True)
def cleanup_test_containers(docker_client):
    """Clean up any test containers after each test."""
    yield

    # Clean up containers with test label
    for container in docker_client.containers.list(all=True):
        if container.name and container.name.startswith("laias-agent-"):
            try:
                container.remove(force=True)
            except Exception:
                pass


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    monkeypatch.setenv("AGENT_CODE_PATH", "/tmp/test-laias-agents")
    monkeypatch.setenv("DOCKER_NETWORK", "laias-test-network")
    return settings
