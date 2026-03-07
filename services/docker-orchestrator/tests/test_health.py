"""
Tests for Docker Orchestrator health endpoints.
"""

import importlib

from app.main import app

TestClient = importlib.import_module("fastapi.testclient").TestClient
client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["service"] == "docker-orchestrator"


def test_health_endpoint():
    """Test health check endpoint returns status info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "version" in data
    assert "docker_connected" in data
    assert data["docker_connected"] is True


def test_containers_list():
    """Test containers list endpoint."""
    response = client.get("/api/containers")
    assert response.status_code == 200
    data = response.json()
    assert "containers" in data
    assert isinstance(data["containers"], list)
