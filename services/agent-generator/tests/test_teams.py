from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.routes.teams import get_db
from app.main import create_app


class _MockScalars:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _MockResult:
    def __init__(self, *, scalar_one_or_none=None, scalar_one=None, scalars_all=None):
        self._scalar_one_or_none = scalar_one_or_none
        self._scalar_one = scalar_one
        self._scalars_all = scalars_all or []

    def scalar_one_or_none(self):
        return self._scalar_one_or_none

    def scalar_one(self):
        return self._scalar_one

    def scalars(self):
        return _MockScalars(self._scalars_all)


class _FakeTeam:
    def __init__(self):
        self.id = uuid4()
        self.name = "Growth Team"
        self.slug = "growth-team"
        self.owner_id = uuid4()
        self.created_at = datetime.now(UTC)


class _FakeUser:
    def __init__(self):
        self.email = "member@laias.local"
        self.name = "Member"


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def client(mock_db):
    app = create_app()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestTeamCrudEndpoints:
    def test_list_teams_success(self, client, mock_db):
        fake_team = _FakeTeam()
        mock_db.execute.side_effect = [
            _MockResult(scalars_all=[fake_team]),
            _MockResult(scalars_all=[SimpleNamespace(), SimpleNamespace()]),
        ]

        response = client.get("/api/teams")

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["name"] == "Growth Team"
        assert payload[0]["members_count"] == 2

    def test_create_team_success(self, client, mock_db):
        def add_side_effect(obj):
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(UTC)
            if getattr(obj, "joined_at", None) is None:
                obj.joined_at = datetime.now(UTC)

        mock_db.execute.return_value = _MockResult(scalar_one_or_none=None)
        mock_db.add.side_effect = add_side_effect

        response = client.post("/api/teams", json={"name": "Ops Team"})

        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Ops Team"
        assert body["slug"] == "ops-team"
        assert body["members_count"] == 1
        mock_db.commit.assert_awaited_once()

    def test_create_team_conflict(self, client, mock_db):
        mock_db.execute.return_value = _MockResult(scalar_one_or_none=_FakeTeam())

        response = client.post("/api/teams", json={"name": "Existing Team", "slug": "growth-team"})

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_team_validation_error(self, client):
        response = client.post("/api/teams", json={})
        assert response.status_code == 422

    def test_get_team_success(self, client, mock_db):
        team = _FakeTeam()
        members_data = [
            {
                "user_id": str(uuid4()),
                "email": "owner@laias.local",
                "name": "Owner",
                "role": "owner",
                "joined_at": datetime.now(UTC).isoformat(),
            }
        ]
        mock_db.execute.side_effect = [
            _MockResult(scalar_one_or_none=team),
            _MockResult(scalar_one_or_none=SimpleNamespace()),
        ]

        with patch(
            "app.api.routes.teams._get_members_with_users", AsyncMock(return_value=members_data)
        ):
            response = client.get(f"/api/teams/{team.id}")

        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] == str(team.id)
        assert payload["members_count"] == 1
        assert payload["members"][0]["role"] == "owner"

    def test_get_team_invalid_id(self, client):
        response = client.get("/api/teams/not-a-uuid")
        assert response.status_code == 404

    def test_update_team_success(self, client, mock_db):
        team = _FakeTeam()
        mock_db.execute.return_value = _MockResult(
            scalars_all=[SimpleNamespace(), SimpleNamespace()]
        )

        with patch(
            "app.api.routes.teams.verify_team_ownership_or_admin",
            AsyncMock(return_value=(team, "owner")),
        ):
            response = client.put(f"/api/teams/{team.id}", json={"name": "Renamed Team"})

        assert response.status_code == 200
        assert response.json()["name"] == "Renamed Team"
        mock_db.commit.assert_awaited()
        mock_db.refresh.assert_awaited()

    def test_delete_team_success(self, client, mock_db):
        team = _FakeTeam()
        with patch("app.api.routes.teams.verify_team_ownership", AsyncMock(return_value=team)):
            response = client.delete(f"/api/teams/{team.id}")

        assert response.status_code == 204
        mock_db.delete.assert_awaited_once_with(team)
        mock_db.commit.assert_awaited()


class TestTeamMembersEndpoints:
    def test_add_team_member_success(self, client, mock_db):
        team = _FakeTeam()
        target_user_id = str(uuid4())

        def add_side_effect(obj):
            if getattr(obj, "joined_at", None) is None:
                obj.joined_at = datetime.now(UTC)

        fake_user = _FakeUser()
        mock_db.execute.side_effect = [
            _MockResult(scalar_one_or_none=fake_user),
            _MockResult(scalar_one_or_none=None),
            _MockResult(scalar_one=fake_user),
        ]
        mock_db.add.side_effect = add_side_effect

        with patch(
            "app.api.routes.teams.verify_team_ownership_or_admin",
            AsyncMock(return_value=(team, "owner")),
        ):
            response = client.post(
                f"/api/teams/{team.id}/members",
                json={"user_id": target_user_id, "role": "member"},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["user_id"] == target_user_id
        assert body["email"] == "member@laias.local"
        assert body["role"] == "member"

    def test_add_team_member_invalid_user_id(self, client):
        team_id = uuid4()
        with patch(
            "app.api.routes.teams.verify_team_ownership_or_admin",
            AsyncMock(return_value=(_FakeTeam(), "owner")),
        ):
            response = client.post(
                f"/api/teams/{team_id}/members",
                json={"user_id": "not-a-uuid", "role": "member"},
            )

        assert response.status_code in (400, 404)

    def test_update_member_role_self_forbidden(self, client):
        team_id = uuid4()
        owner_id = "00000000-0000-0000-0000-000000000000"

        with patch(
            "app.api.routes.teams.verify_team_ownership", AsyncMock(return_value=_FakeTeam())
        ):
            response = client.put(
                f"/api/teams/{team_id}/members/{owner_id}",
                json={"role": "admin"},
                headers={"X-User-Id": owner_id},
            )

        assert response.status_code == 400
        assert "owner cannot change" in response.json()["detail"].lower()

    def test_remove_team_member_invalid_id(self, client):
        team_id = uuid4()
        response = client.delete(f"/api/teams/{team_id}/members/not-a-uuid")
        assert response.status_code == 400
