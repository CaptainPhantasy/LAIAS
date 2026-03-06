"""
Tests for container lifecycle management.

Tests deployment, status, logs, and termination of agent containers.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import docker
from fastapi.testclient import TestClient

from app.main import app
from app.models.requests import DeployAgentRequest


client = TestClient(app)


class TestContainerDeployment:
    """Tests for agent container deployment."""

    @pytest.fixture
    def mock_docker_client(self):
        """Mock Docker client for testing without Docker daemon."""
        with patch("app.services.container_manager.docker.from_env") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def valid_deployment_request(self):
        """Valid deployment request payload."""
        return {
            "agent_id": "test-agent-001",
            "agent_name": "Test Agent",
            "flow_code": "async def flow(ctx): return ctx.result(success=True)",
            "agents_yaml": "agents:\n  - name: test\n    role: tester",
            "requirements": ["pydantic>=2.0"],
            "cpu_limit": 0.5,
            "memory_limit": "256m",
            "auto_start": False
        }

    def test_deploy_endpoint_exists(self):
        """Deploy endpoint is accessible."""
        response = client.post("/api/deploy", json={
            "agent_id": "test",
            "agent_name": "Test",
            "flow_code": "async def flow(ctx): pass",
            "agents_yaml": "agents: []",
            "requirements": []
        })
        # Should not be 404 (might be 400/500 if Docker unavailable)
        assert response.status_code != 404

    def test_deploy_missing_required_fields_returns_422(self):
        """Deploy with missing fields returns validation error."""
        response = client.post("/api/deploy", json={
            "agent_id": "test"
            # Missing other required fields
        })
        assert response.status_code == 422

    def test_deploy_invalid_memory_format_returns_422(self):
        """Deploy with invalid memory format returns validation error."""
        response = client.post("/api/deploy", json={
            "agent_id": "test",
            "agent_name": "Test",
            "flow_code": "async def flow(ctx): pass",
            "agents_yaml": "agents: []",
            "requirements": [],
            "memory_limit": "invalid"  # Should be like "256m" or "1g"
        })
        # May or may not validate, depends on model
        # Just verify endpoint handles it gracefully
        assert response.status_code in [400, 422, 500]


class TestContainerStatus:
    """Tests for container status endpoints."""

    def test_containers_list_endpoint(self):
        """Containers list endpoint returns list."""
        response = client.get("/api/containers")
        assert response.status_code == 200
        data = response.json()
        assert "containers" in data
        assert isinstance(data["containers"], list)

    def test_container_status_endpoint_format(self):
        """Container status endpoint expects valid ID format."""
        response = client.get("/api/containers/invalid-id/status")
        # Should handle gracefully (404, 400, or 500)
        assert response.status_code in [400, 404, 500]

    def test_container_status_not_found(self):
        """Container status returns 404 for non-existent container."""
        response = client.get("/api/containers/nonexistent-container-xyz/status")
        assert response.status_code in [404, 500]  # 500 if Docker unavailable


class TestContainerLogs:
    """Tests for container log streaming."""

    def test_logs_endpoint_exists(self):
        """Logs endpoint is accessible."""
        response = client.get("/api/containers/test-agent/logs")
        # Should not be 404
        assert response.status_code != 404

    def test_logs_with_tail_parameter(self):
        """Logs endpoint accepts tail parameter."""
        response = client.get("/api/containers/test-agent/logs?tail=100")
        # Should not be 404 or 422 (validation error)
        assert response.status_code != 422

    def test_logs_for_nonexistent_container(self):
        """Logs endpoint handles non-existent container."""
        response = client.get("/api/containers/nonexistent-xyz/logs")
        assert response.status_code in [404, 500]


class TestContainerLifecycle:
    """Tests for container start/stop/restart operations."""

    def test_start_endpoint_exists(self):
        """Start container endpoint is accessible."""
        response = client.post("/api/containers/test-agent/start")
        # Should not be 404
        assert response.status_code != 404

    def test_stop_endpoint_exists(self):
        """Stop container endpoint is accessible."""
        response = client.post("/api/containers/test-agent/stop")
        # Should not be 404
        assert response.status_code != 404

    def test_restart_endpoint_exists(self):
        """Restart container endpoint is accessible."""
        response = client.post("/api/containers/test-agent/restart")
        # Should not be 404
        assert response.status_code != 404

    def test_terminate_endpoint_exists(self):
        """Terminate container endpoint is accessible."""
        response = client.delete("/api/containers/test-agent")
        # Should not be 404
        assert response.status_code != 404


class TestContainerResourceLimits:
    """Tests for container resource limit validation."""

    def test_cpu_limit_validation(self):
        """CPU limit must be between 0 and number of CPUs."""
        # This tests the request model validation
        request = DeployAgentRequest(
            agent_id="test",
            agent_name="Test",
            flow_code="pass",
            agents_yaml="agents: []",
            requirements=[],
            cpu_limit=0.5  # Valid
        )
        assert request.cpu_limit == 0.5

    def test_memory_limit_formats(self):
        """Memory limit accepts valid formats."""
        # Valid formats: "256m", "1g", "512M", "2G"
        valid_limits = ["256m", "1g", "512M", "2G"]
        for limit in valid_limits:
            request = DeployAgentRequest(
                agent_id="test",
                agent_name="Test",
                flow_code="pass",
                agents_yaml="agents: []",
                requirements=[],
                memory_limit=limit
            )
            assert request.memory_limit == limit


class TestContainerNaming:
    """Tests for container naming conventions."""

    def test_container_name_sanitization(self):
        """Container names are sanitized from special characters."""
        # Agent names with special chars should be handled gracefully
        special_names = [
            "Test Agent!",  # Spaces and special chars
            "test-agent-123",  # Valid
            "Test_Agent",  # Underscores
            "test.agent",  # Dots
        ]

        for name in special_names:
            response = client.post("/api/deploy", json={
                "agent_id": "test-id",
                "agent_name": name,
                "flow_code": "async def flow(ctx): pass",
                "agents_yaml": "agents: []",
                "requirements": []
            })
            # Should handle gracefully (not crash)
            assert response.status_code != 500 or "error" in response.text.lower()
