from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class _FakeTool:
    def __init__(self, name: str, category: str, available: bool):
        self.name = name
        self.category = SimpleNamespace(value=category)
        self.description = f"{name} description"
        self.dependencies = ["requests"]
        self._available = available

    def is_available(self, _env):
        return self._available

    def get_missing_config(self, _env):
        return [] if self._available else ["API_KEY"]


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestToolsRegistryEndpoints:
    def test_list_tools_success(self, client):
        listed_tools = [
            {
                "name": "WebTool",
                "category": "web",
                "description": "web helper",
                "available": True,
                "missing_config": [],
                "dependencies": [],
            }
        ]
        with (
            patch("app.api.routes.tools.list_available_tools", return_value=listed_tools),
            patch("app.api.routes.tools.get_tool_registry") as mock_get_registry,
        ):
            mock_get_registry.return_value.get_category_summary.return_value = {
                "web": {"total": 1, "available": 1}
            }

            response = client.get("/tools/")

        assert response.status_code == 200
        payload = response.json()
        assert payload["total_tools"] == 1
        assert payload["available_tools"] == 1
        assert payload["tools"][0]["name"] == "WebTool"

    def test_list_categories_success(self, client):
        fake_tool = _FakeTool(name="SearchTool", category="search", available=True)
        with patch("app.api.routes.tools.get_tool_registry") as mock_get_registry:
            mock_get_registry.return_value.get_tools_by_category.return_value = [fake_tool]

            response = client.get("/tools/categories")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all("category" in item for item in data)
        assert all("available_tools" in item for item in data)

    def test_get_tools_in_category_success(self, client):
        unavailable_tool = _FakeTool(name="DBTool", category="database", available=False)
        with patch("app.api.routes.tools.get_tools_by_category", return_value=[unavailable_tool]):
            response = client.get("/tools/category/database")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["name"] == "DBTool"
        assert body[0]["available"] is False
        assert body[0]["missing_config"] == ["API_KEY"]

    def test_list_available_and_unavailable_success(self, client):
        available_tool = _FakeTool(name="MailTool", category="integration", available=True)
        fake_registry = SimpleNamespace(
            get_available_tools=lambda _env: [available_tool],
            get_unavailable_tools=lambda _env: {"SecretTool": ["SECRET_KEY"]},
        )
        with patch("app.api.routes.tools.get_tool_registry", return_value=fake_registry):
            available_response = client.get("/tools/available")
            unavailable_response = client.get("/tools/unavailable")

        assert available_response.status_code == 200
        assert available_response.json()[0]["name"] == "MailTool"
        assert unavailable_response.status_code == 200
        assert unavailable_response.json()["SecretTool"] == ["SECRET_KEY"]

    def test_get_tool_info_success_and_not_found(self, client):
        fake_registry = SimpleNamespace(get_tool=lambda name: _FakeTool(name, "web", True))
        with patch("app.api.routes.tools.get_tool_registry", return_value=fake_registry):
            response = client.get("/tools/MyTool")

        assert response.status_code == 200
        assert response.json()["name"] == "MyTool"

        missing_registry = SimpleNamespace(get_tool=lambda _name: None)
        with patch("app.api.routes.tools.get_tool_registry", return_value=missing_registry):
            missing = client.get("/tools/MissingTool")

        assert missing.status_code == 404


class TestToolInstantiation:
    def test_instantiate_tool_success(self, client):
        mock_instance = AsyncMock()
        fake_registry = SimpleNamespace(instantiate_tool=lambda *_args, **_kwargs: mock_instance)

        with patch("app.api.routes.tools.get_tool_registry", return_value=fake_registry):
            response = client.post(
                "/tools/instantiate",
                json={"tool_name": "MyTool", "config": {"api_key": "x"}},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["tool_name"] == "MyTool"

    def test_instantiate_tool_validation_error(self, client):
        response = client.post("/tools/instantiate", json={"config": {"api_key": "x"}})
        assert response.status_code == 422
