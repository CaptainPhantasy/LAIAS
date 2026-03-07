import importlib
from unittest.mock import AsyncMock, MagicMock

pytest = importlib.import_module("pytest")

from app.api.routes import outputs as outputs_routes


@pytest.fixture
def mock_output_service(monkeypatch):
    service = MagicMock()
    service.persist_event = AsyncMock(return_value={"postgres": True, "files": False})
    service.list_runs.return_value = []
    service.get_run_detail.return_value = {
        "deployment_id": "dep-1",
        "run_id": "run-1",
        "summary_markdown": "",
        "metrics": {},
        "events": [],
    }
    monkeypatch.setattr(outputs_routes, "get_output_persistence_service", lambda: service)
    return service


def test_ingest_output_event_accepts_valid_payload(client, mock_output_service):
    payload = {
        "run_id": "run-123",
        "event_type": "run_started",
        "level": "INFO",
        "message": "Started",
        "source": "agent",
        "payload": {"step": 1},
    }

    response = client.post("/api/deployments/dep-123/outputs/events", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["deployment_id"] == "dep-123"
    assert data["run_id"] == "run-123"
    assert data["accepted"] is True
    assert data["destinations"] == {"postgres": True, "files": False}
    assert mock_output_service.persist_event.await_count == 1


def test_ingest_output_event_validation_error(client):
    response = client.post(
        "/api/deployments/dep-123/outputs/events",
        json={"event_type": "run_started", "message": "Missing run id"},
    )
    assert response.status_code == 422


def test_list_output_runs_returns_normalized_items(client, mock_output_service):
    mock_output_service.list_runs.return_value = [
        {"run_id": "run-1", "has_summary": True, "has_metrics": False, "event_count": 4},
        {
            "run_id": "run-2",
            "has_summary": 1,
            "has_metrics": "",
            "event_count": "not-an-int",
        },
    ]

    response = client.get("/api/deployments/dep-1/outputs/runs")

    assert response.status_code == 200
    data = response.json()
    assert data["deployment_id"] == "dep-1"
    assert len(data["runs"]) == 2
    assert data["runs"][0] == {
        "run_id": "run-1",
        "has_summary": True,
        "has_metrics": False,
        "event_count": 4,
    }
    assert data["runs"][1] == {
        "run_id": "run-2",
        "has_summary": True,
        "has_metrics": False,
        "event_count": 0,
    }


def test_get_output_run_detail_returns_normalized_detail(client, mock_output_service):
    mock_output_service.list_runs.return_value = [{"run_id": "run-1"}]
    mock_output_service.get_run_detail.return_value = {
        "deployment_id": "dep-1",
        "run_id": "run-1",
        "summary_markdown": "# Summary",
        "metrics": "invalid",
        "events": "invalid",
    }

    response = client.get("/api/deployments/dep-1/outputs/runs/run-1")

    assert response.status_code == 200
    data = response.json()
    assert data["deployment_id"] == "dep-1"
    assert data["run_id"] == "run-1"
    assert data["summary_markdown"] == "# Summary"
    assert data["metrics"] == {}
    assert data["events"] == []


def test_get_output_run_detail_returns_404_for_missing_run(client, mock_output_service):
    mock_output_service.list_runs.return_value = [{"run_id": "run-1"}]

    response = client.get("/api/deployments/dep-1/outputs/runs/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Run not found"
