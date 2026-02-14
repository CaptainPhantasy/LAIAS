"""
Tests for code validation endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(create_app())


def test_validate_code_success(client):
    """Test successful code validation."""
    request_data = {
        "code": """
class TestFlow(Flow[AgentState]):
    @start()
    async def begin(self):
        pass
""",
        "check_pattern_compliance": True,
        "check_syntax": True
    }

    response = client.post("/api/validate-code", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "pattern_compliance_score" in data


def test_validate_code_syntax_error(client):
    """Test validation with syntax error."""
    request_data = {
        "code": "def broken(:",
        "check_syntax": True
    }

    response = client.post("/api/validate-code", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert len(data["syntax_errors"]) > 0


def test_validation_rules_endpoint(client):
    """Test validation rules endpoint."""
    response = client.get("/api/validation-rules")
    assert response.status_code == 200
    data = response.json()
    assert "required_patterns" in data
    assert "recommended_patterns" in data
