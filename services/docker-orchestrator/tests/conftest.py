"""Pytest configuration and fixtures."""

import importlib
from unittest.mock import MagicMock

docker = importlib.import_module("docker")
pytest = importlib.import_module("pytest")
TestClient = importlib.import_module("fastapi.testclient").TestClient
NotFound = docker.errors.NotFound

from app.config import settings
from app.database.session import get_db
from app.main import app


def _docker_available() -> bool:
    """Check if Docker daemon is reachable."""
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


# Module-level flag so we only probe Docker once per session
DOCKER_AVAILABLE = _docker_available()


@pytest.fixture(autouse=True)
def mock_docker_globally(monkeypatch):
    """Mock docker.from_env globally so tests don't need a real Docker daemon."""
    if DOCKER_AVAILABLE:
        return

    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.containers.list.return_value = []

    mock_container = MagicMock(
        id="mock-container-id",
        name="laias-agent-test",
        status="created",
        labels={
            "deployment_id": "mock-deployment-id",
            "agent_id": "test",
            "agent_name": "Test",
            "laias": "agent",
        },
        attrs={
            "Created": "2026-01-01T00:00:00Z",
            "State": {"StartedAt": "2026-01-01T00:00:00Z"},
        },
    )
    mock_container.logs.return_value = b""
    mock_container.start.return_value = None
    mock_container.stop.return_value = None
    mock_container.restart.return_value = None
    mock_container.remove.return_value = None

    mock_client.containers.create.return_value = mock_container

    def _mock_get_container(container_id: str):
        if "nonexistent" in container_id or "invalid" in container_id:
            raise NotFound("Not found")
        return mock_container

    mock_client.containers.get.side_effect = _mock_get_container

    # Reset the service singletons
    import app.services.container_manager as cm_mod
    import app.services.docker_service as ds_mod

    ds_mod._docker_service = None
    cm_mod._container_manager = None

    monkeypatch.setattr("docker.from_env", lambda **kwargs: mock_client)
    monkeypatch.setattr("docker.DockerClient.from_env", lambda **kwargs: mock_client)

    yield mock_client

    # Reset singletons after test
    ds_mod._docker_service = None
    cm_mod._container_manager = None


@pytest.fixture(autouse=True)
def mock_db_dependency():
    """Override DB dependency to avoid requiring greenlet-backed SQLAlchemy sessions."""

    class _DummySession:
        async def execute(self, *args, **kwargs):
            return None

        async def commit(self):
            return None

        async def rollback(self):
            return None

    async def _override_get_db():
        yield _DummySession()

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def docker_client():
    """Docker client for testing — skips if Docker is unreachable."""
    if not DOCKER_AVAILABLE:
        pytest.skip("Docker daemon not available")
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
    return """
version: "1.0"
agents:
  - name: test_agent
    role: Test agent for orchestrator
    instructions: You are a helpful test agent
"""


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
def cleanup_test_containers():
    """Clean up any test containers after each test."""
    yield

    if not DOCKER_AVAILABLE:
        return

    try:
        dc = docker.from_env()
        for container in dc.containers.list(all=True):
            if container.name and container.name.startswith("laias-agent-"):
                try:
                    container.remove(force=True)
                except Exception:
                    pass
    except Exception:
        pass


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    monkeypatch.setenv("AGENT_CODE_PATH", "/tmp/test-laias-agents")
    monkeypatch.setenv("DOCKER_NETWORK", "laias-test-network")
    return settings
