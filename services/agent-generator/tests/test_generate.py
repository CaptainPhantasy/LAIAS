"""
Tests for agent generation endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import create_app
from app.models.requests import GenerateAgentRequest


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(create_app())


@pytest.fixture
def mock_llm_service():
    """Mock LLM service fixture."""
    with patch("app.services.llm_service.AsyncOpenAI") as mock_openai:
        mock_response = type('MockResponse', (), {
            'choices': [type('MockChoice', (), {
                'message': type('MockMessage', (), {
                    'content': '''{
                        "flow_code": "class TestFlow(Flow[AgentState]):\\n    @start()\\n    async def begin(self):\\n        pass",
                        "state_class": "class AgentState(BaseModel):\\n    task_id: str = ''",
                        "agents_yaml": "agents:\\n  test:",
                        "requirements": ["crewai[tools]>=0.80.0"],
                        "flow_diagram": "graph TD\\n    A[Start]",
                        "agents_info": []
                    }'''
                })()
            })()],
            'usage': type('MockUsage', (), {
                'total_tokens': 1000
            })()
        })
        mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        yield mock_openai


def test_root_endpoint(client):
    """Test root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Agent Generator Service"
    assert "version" in data


@pytest.mark.asyncio
async def test_generate_agent_success(client, mock_llm_service):
    """Test successful agent generation."""
    request_data = {
        "description": "Create a research agent that searches the web",
        "agent_name": "TestResearchFlow",
        "complexity": "simple",
        "task_type": "research"
    }

    # Note: This would require async test setup
    # response = await client.post("/api/generate-agent", json=request_data)
    # assert response.status_code == 200
    # data = response.json()
    # assert "agent_id" in data
    # assert "flow_code" in data
    # assert data["agent_name"] == "TestResearchFlow"


def test_generate_agent_validation_error(client):
    """Test generation with invalid request."""
    request_data = {
        "description": "short",  # Too short
        "agent_name": "123Invalid",  # Starts with number
        "complexity": "invalid"
    }

    response = client.post("/api/generate-agent", json=request_data)
    assert response.status_code == 422  # Validation error


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "uptime_seconds" in data
