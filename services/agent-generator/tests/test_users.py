import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestCurrentUserEndpoints:
    def test_get_current_user_success(self, client):
        response = client.get("/api/users/me")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "00000000-0000-0000-0000-000000000000"
        assert body["email"] == "dev@laias.local"
        assert body["name"] == "Dev User"

    def test_get_current_user_with_headers_success(self, client):
        headers = {
            "X-User-Id": "11111111-1111-1111-1111-111111111111",
            "X-User-Email": "tester@laias.local",
            "X-User-Name": "Test User",
        }
        response = client.get("/api/users/me", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "11111111-1111-1111-1111-111111111111"
        assert body["email"] == "tester@laias.local"
        assert body["name"] == "Test User"

    def test_update_current_user_success(self, client):
        response = client.put(
            "/api/users/me",
            json={"email": "updated@laias.local", "name": "Updated Name"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "updated@laias.local"
        assert body["name"] == "Updated Name"

    def test_update_current_user_validation_error(self, client):
        response = client.put("/api/users/me", json={"name": {"first": "Invalid"}})
        assert response.status_code == 422
