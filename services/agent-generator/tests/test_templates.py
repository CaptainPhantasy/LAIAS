from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestTemplatesList:
    def test_list_templates_success(self, client):
        fake_templates = [
            {
                "id": "tmpl_1",
                "name": "Lead Qualifier",
                "description": "Template description",
                "category": "sales",
                "tags": ["lead", "sales"],
                "default_complexity": "moderate",
                "default_tools": ["SerperDevTool"],
                "sample_prompts": ["Build a lead qualification agent"],
                "suggested_config": {"max_agents": 3},
                "agent_structure": {"roles": ["researcher"]},
                "expected_outputs": ["qualified leads"],
            }
        ]
        with patch("app.api.routes.templates.get_template_service") as mock_get_service:
            mock_service = mock_get_service.return_value
            mock_service.list_templates.return_value = fake_templates
            mock_service.list_categories.return_value = ["sales", "support"]

            response = client.get("/api/templates?category=sales&search=lead")

        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 1
        assert payload["templates"][0]["id"] == "tmpl_1"
        assert payload["categories"] == ["sales", "support"]

    def test_list_categories_success(self, client):
        with patch("app.api.routes.templates.get_template_service") as mock_get_service:
            mock_service = mock_get_service.return_value
            mock_service.list_categories.return_value = ["sales", "support"]

            response = client.get("/api/templates/categories")

        assert response.status_code == 200
        body = response.json()
        assert body["categories"] == ["sales", "support"]
        assert body["total"] == 2


class TestTemplateGetAndApply:
    def test_get_template_success(self, client):
        template = {
            "id": "tmpl_2",
            "name": "Outreach",
            "description": "Outreach helper",
            "category": "sales",
            "tags": ["outreach"],
            "default_complexity": "simple",
            "default_tools": [],
            "sample_prompts": ["Create outreach flow"],
            "suggested_config": {},
            "agent_structure": {},
            "expected_outputs": ["messages"],
        }
        with patch("app.api.routes.templates.get_template_service") as mock_get_service:
            mock_get_service.return_value.get_template.return_value = template

            response = client.get("/api/templates/tmpl_2")

        assert response.status_code == 200
        assert response.json()["name"] == "Outreach"

    def test_get_template_not_found(self, client):
        with patch("app.api.routes.templates.get_template_service") as mock_get_service:
            mock_get_service.return_value.get_template.return_value = None

            response = client.get("/api/templates/missing")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_apply_template_success(self, client):
        template = {
            "id": "tmpl_apply",
            "name": "Apply Me",
            "description": "Generate something useful",
            "category": "research",
            "tags": [],
            "default_complexity": "moderate",
            "default_tools": ["SerperDevTool"],
            "sample_prompts": ["Research regional market signals in depth"],
            "suggested_config": {"llm_provider": "zai", "include_memory": True, "max_agents": 2},
            "agent_structure": {},
            "expected_outputs": [],
        }
        with patch("app.api.routes.templates.get_template_service") as mock_get_service:
            mock_get_service.return_value.get_template.return_value = template

            response = client.post(
                "/api/templates/tmpl_apply/apply",
                json={
                    "template_id": "tmpl_apply",
                    "agent_name": "TemplateFlow",
                    "customizations": {"task_type": "analysis", "max_agents": 4},
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["agent_name"] == "TemplateFlow"
        assert body["complexity"] == "moderate"
        assert body["task_type"] == "analysis"
        assert body["max_agents"] == 4

    def test_apply_template_not_found(self, client):
        with patch("app.api.routes.templates.get_template_service") as mock_get_service:
            mock_get_service.return_value.get_template.return_value = None

            response = client.post(
                "/api/templates/missing/apply",
                json={"template_id": "missing", "agent_name": "ValidFlow"},
            )

        assert response.status_code == 404

    def test_apply_template_validation_error(self, client):
        response = client.post(
            "/api/templates/tmpl_apply/apply",
            json={"template_id": "tmpl_apply"},
        )
        assert response.status_code == 422
