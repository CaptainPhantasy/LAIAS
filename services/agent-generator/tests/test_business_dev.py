import pytest
from fastapi.testclient import TestClient

from app.api.routes.business_dev import router as business_dev_router
from app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    app.include_router(business_dev_router)
    return TestClient(app)


class TestBusinessDevCampaignRoutes:
    def test_start_campaign_success(self, client):
        response = client.post(
            "/api/business-dev-campaign",
            json={
                "target_industries": ["Healthcare", "Manufacturing"],
                "target_geography": "Indiana",
            },
        )

        assert response.status_code == 303
        body = response.json()
        assert body["status"] == "redirect"
        assert body["deploy_url"] == "/api/deploy"
        assert body["suggested_payload"]["agent_name"] == "indiana_smb_business_development"

    def test_start_campaign_validation_error(self, client):
        response = client.post(
            "/api/business-dev-campaign",
            json={"target_geography": ["Indiana"]},
        )
        assert response.status_code == 422

    def test_get_campaign_status_success(self, client):
        response = client.get("/api/business-dev-campaign/agent-123")

        assert response.status_code == 303
        body = response.json()
        assert body["status"] == "redirect"
        assert body["container_url"] == "/api/containers/agent-123"

    def test_stop_campaign_success(self, client):
        response = client.post("/api/business-dev-campaign/agent-123/stop")

        assert response.status_code == 303
        body = response.json()
        assert body["status"] == "redirect"
        assert body["stop_url"] == "/api/containers/agent-123/stop"
