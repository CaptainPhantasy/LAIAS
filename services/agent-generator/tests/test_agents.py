from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.routes.agents import get_db
from app.main import create_app


class _MockScalars:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _MockResult:
    def __init__(
        self,
        *,
        scalar_one_or_none=None,
        scalar=None,
        scalars_all=None,
    ):
        self._scalar_one_or_none = scalar_one_or_none
        self._scalar = scalar
        self._scalars_all = scalars_all or []

    def scalar_one_or_none(self):
        return self._scalar_one_or_none

    def scalar(self):
        return self._scalar

    def scalars(self):
        return _MockScalars(self._scalars_all)


class _FakeAgent:
    def __init__(self, agent_id: str = "gen_123", owner_id: str | None = None):
        now = datetime.now(UTC)
        self.id = agent_id
        self.name = "TestFlow"
        self.description = "A valid test agent description"
        self.flow_code = "class TestFlow: pass"
        self.agents_yaml = "agents: {}"
        self.state_class = "class AgentState: pass"
        self.complexity = "moderate"
        self.task_type = "general"
        self.requirements = ["crewai"]
        self.llm_provider = "zai"
        self.model = "glm-5"
        self.estimated_cost_per_run = 0.1
        self.complexity_score = 3
        self.validation_status = {"is_valid": True}
        self.flow_diagram = "graph TD"
        self.version = 2
        self.latest_version = 3
        self.is_active = True
        self.deployed_count = 0
        self.last_deployed = None
        self.created_at = now
        self.updated_at = now
        self.owner_id = owner_id
        self.team_id = None

    def to_dict(self):
        return {
            "agent_id": self.id,
            "agent_name": self.name,
            "description": self.description,
            "flow_code": self.flow_code,
            "agents_yaml": self.agents_yaml,
            "state_class": self.state_class,
            "complexity": self.complexity,
            "task_type": self.task_type,
            "requirements": self.requirements,
            "llm_provider": self.llm_provider,
            "model": self.model,
            "estimated_cost_per_run": self.estimated_cost_per_run,
            "complexity_score": self.complexity_score,
            "validation_status": self.validation_status,
            "flow_diagram": self.flow_diagram,
            "version": self.version,
            "latest_version": self.latest_version,
            "is_active": self.is_active,
            "deployed_count": self.deployed_count,
            "last_deployed": self.last_deployed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "owner_id": self.owner_id,
            "team_id": str(self.team_id) if self.team_id else None,
        }


class _FakeVersion:
    def __init__(self, agent_id: str, version: int):
        self.id = version
        self.agent_id = agent_id
        self.version = version
        self.flow_code = f"class TestFlowV{version}: pass"
        self.agents_yaml = "agents: {}"
        self.state_class = "class AgentState: pass"
        self.requirements = ["crewai"]
        self.validation_status = {"is_valid": True}
        self.flow_diagram = "graph TD"
        self.created_at = datetime.now(UTC)
        self.change_summary = f"Version {version}"

    def to_dict(self):
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "version": self.version,
            "flow_code": self.flow_code,
            "agents_yaml": self.agents_yaml,
            "state_class": self.state_class,
            "requirements": self.requirements,
            "validation_status": self.validation_status,
            "flow_diagram": self.flow_diagram,
            "created_at": self.created_at.isoformat(),
            "change_summary": self.change_summary,
        }


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def client(mock_db):
    app = create_app()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestAgentsListAndGet:
    def test_list_agents_success(self, client, mock_db):
        fake_agent = _FakeAgent()
        mock_db.execute.side_effect = [
            _MockResult(scalar=1),
            _MockResult(scalars_all=[fake_agent]),
        ]

        response = client.get("/api/agents?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["limit"] == 10
        assert len(data["agents"]) == 1
        assert data["agents"][0]["agent_id"] == "gen_123"

    def test_list_agents_invalid_limit_returns_422(self, client):
        response = client.get("/api/agents?limit=0")
        assert response.status_code == 422

    def test_get_agent_success(self, client, mock_db):
        mock_db.execute.return_value = _MockResult(scalar_one_or_none=_FakeAgent())

        response = client.get("/api/agents/gen_123")

        assert response.status_code == 200
        assert response.json()["agent_id"] == "gen_123"

    def test_get_agent_not_found(self, client, mock_db):
        mock_db.execute.return_value = _MockResult(scalar_one_or_none=None)

        response = client.get("/api/agents/missing")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAgentVersions:
    def test_list_agent_versions_success(self, client, mock_db):
        agent = _FakeAgent()
        old_version = _FakeVersion(agent.id, 1)
        current_version = _FakeVersion(agent.id, agent.version)
        mock_db.execute.side_effect = [
            _MockResult(scalar_one_or_none=agent),
            _MockResult(scalars_all=[old_version, current_version]),
        ]

        response = client.get(f"/api/agents/{agent.id}/versions")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent.id
        assert data["current_version"] == 2
        assert any(version["is_current"] for version in data["versions"])

    def test_get_specific_version_not_found(self, client, mock_db):
        agent = _FakeAgent()
        mock_db.execute.side_effect = [
            _MockResult(scalar_one_or_none=agent),
            _MockResult(scalar_one_or_none=None),
        ]

        response = client.get(f"/api/agents/{agent.id}/versions/7")

        assert response.status_code == 404
        assert "version" in response.json()["detail"].lower()

    def test_rollback_agent_version_success(self, client, mock_db):
        agent = _FakeAgent()
        target = _FakeVersion(agent.id, 1)
        mock_db.execute.side_effect = [
            _MockResult(scalar_one_or_none=agent),
            _MockResult(scalar_one_or_none=target),
            _MockResult(scalar_one_or_none=None),
        ]

        response = client.post(f"/api/agents/{agent.id}/versions/1/rollback")

        assert response.status_code == 200
        body = response.json()
        assert body["agent_id"] == agent.id
        assert body["rolled_back_to_version"] == 1
        assert body["new_version"] == 4
        mock_db.commit.assert_awaited_once()


class TestAgentUpdateDelete:
    def test_update_agent_success(self, client, mock_db):
        agent = _FakeAgent()
        mock_db.execute.return_value = _MockResult(scalar_one_or_none=agent)

        response = client.put(
            f"/api/agents/{agent.id}",
            json={"description": "Updated description for this test agent", "is_active": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description for this test agent"
        assert data["is_active"] is False
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    def test_update_agent_validation_error(self, client):
        response = client.put(
            "/api/agents/gen_123",
            json={"description": "short"},
        )
        assert response.status_code == 422

    def test_delete_agent_not_found(self, client, mock_db):
        mock_db.execute.return_value = _MockResult(scalar_one_or_none=None)

        response = client.delete("/api/agents/missing")

        assert response.status_code == 404


class TestAgentSharing:
    def test_share_agent_missing_team_id_returns_422(self, client, mock_db):
        mock_db.execute.return_value = _MockResult(scalar_one_or_none=_FakeAgent())

        response = client.post("/api/agents/gen_123/share")

        assert response.status_code == 422

    def test_share_agent_success(self, client, mock_db):
        owner_id = str(uuid4())
        team_id = str(uuid4())
        agent = _FakeAgent(owner_id=owner_id)

        mock_db.execute.side_effect = [
            _MockResult(scalar_one_or_none=agent),
            _MockResult(scalar_one_or_none=SimpleNamespace()),
        ]

        with patch("sqlalchemy.cast", side_effect=lambda value, _type: value):
            response = client.post(
                f"/api/agents/{agent.id}/share?team_id={team_id}",
                headers={"X-User-Id": owner_id},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["team_id"] == team_id
        mock_db.commit.assert_awaited()
