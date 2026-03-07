import importlib
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

pytest = importlib.import_module("pytest")

from app.api.routes import analytics as analytics_routes


def test_usage_stats_returns_aggregated_metrics(client, monkeypatch):
    now = datetime.now(UTC)
    events = [
        {
            "event_type": "api_call",
            "event_data": {"endpoint": "/api/deploy", "response_time_ms": 110},
            "created_at": now - timedelta(days=1),
        },
        {
            "event_type": "llm_call",
            "event_data": {
                "provider": "openai",
                "model": "default",
                "input_tokens": 1000,
                "output_tokens": 500,
            },
            "created_at": now - timedelta(days=1),
        },
    ]
    mock_get_events = AsyncMock(return_value=events)
    monkeypatch.setattr(analytics_routes.analytics_store, "get_events_since", mock_get_events)

    response = client.get("/api/analytics/usage?days=3")

    assert response.status_code == 200
    data = response.json()
    assert data["period_days"] == 3
    assert data["total_api_calls"] == 1
    assert data["total_tokens_used"] == 1500
    assert data["api_calls_by_endpoint"] == {"/api/deploy": 1}
    assert data["tokens_by_provider"]["openai"] == {"input": 1000, "output": 500}
    assert len(data["daily_timeseries"]) == 3


def test_usage_stats_provider_filter(client, monkeypatch):
    now = datetime.now(UTC)
    mock_get_events = AsyncMock(
        return_value=[
            {
                "event_type": "llm_call",
                "event_data": {
                    "provider": "openai",
                    "model": "default",
                    "input_tokens": 200,
                    "output_tokens": 100,
                },
                "created_at": now,
            },
            {
                "event_type": "llm_call",
                "event_data": {
                    "provider": "anthropic",
                    "model": "default",
                    "input_tokens": 400,
                    "output_tokens": 300,
                },
                "created_at": now,
            },
        ]
    )
    monkeypatch.setattr(analytics_routes.analytics_store, "get_events_since", mock_get_events)

    response = client.get("/api/analytics/usage?days=2&provider=openai")

    assert response.status_code == 200
    data = response.json()
    assert data["total_tokens_used"] == 300
    assert set(data["tokens_by_provider"].keys()) == {"openai"}


def test_usage_stats_validation_error(client):
    response = client.get("/api/analytics/usage?days=invalid")
    assert response.status_code == 422


def test_deployment_stats_returns_distribution(client, monkeypatch):
    now = datetime.now(UTC)
    mock_get_events = AsyncMock(
        return_value=[
            {
                "event_type": "deployment",
                "event_data": {
                    "deployment_id": "dep-1",
                    "agent_id": "a-1",
                    "agent_name": "Agent A",
                    "status": "running",
                },
                "created_at": now - timedelta(days=1),
            },
            {
                "event_type": "deployment",
                "event_data": {
                    "deployment_id": "dep-2",
                    "agent_id": "a-2",
                    "agent_name": "Agent B",
                    "status": "error",
                },
                "created_at": now,
            },
        ]
    )
    monkeypatch.setattr(analytics_routes.analytics_store, "get_events_since", mock_get_events)

    response = client.get("/api/analytics/deployments?days=2")

    assert response.status_code == 200
    data = response.json()
    assert data["total_deployments"] == 2
    assert data["successful_deployments"] == 1
    assert data["failed_deployments"] == 1
    assert data["success_rate"] == 50.0
    assert data["deployments_by_status"] == {"running": 1, "error": 1}
    assert len(data["daily_timeseries"]) == 2
    assert len(data["recent_deployments"]) == 2


def test_deployment_stats_validation_error(client):
    response = client.get("/api/analytics/deployments?days=invalid")
    assert response.status_code == 422


def test_performance_metrics_returns_percentiles(client, monkeypatch):
    now = datetime.now(UTC)
    mock_get_events = AsyncMock(
        return_value=[
            {
                "event_type": "api_call",
                "event_data": {"response_time_ms": 100},
                "created_at": now,
            },
            {
                "event_type": "api_call",
                "event_data": {"response_time_ms": 300},
                "created_at": now,
            },
            {
                "event_type": "api_call",
                "event_data": {"response_time_ms": 200},
                "created_at": now,
            },
        ]
    )
    monkeypatch.setattr(analytics_routes.analytics_store, "get_events_since", mock_get_events)

    response = client.get("/api/analytics/performance?days=1")

    assert response.status_code == 200
    data = response.json()
    assert data["period_days"] == 1
    assert data["total_requests"] == 3
    assert data["avg_response_time_ms"] == 200.0
    assert data["p50_response_time_ms"] == 200.0
    assert data["p95_response_time_ms"] == 300.0
    assert data["p99_response_time_ms"] == 300.0
    assert len(data["daily_timeseries"]) == 1


def test_performance_metrics_validation_error(client):
    response = client.get("/api/analytics/performance?days=invalid")
    assert response.status_code == 422


def test_record_event_accepts_valid_payload(client, monkeypatch):
    mock_add_event = AsyncMock(return_value={})
    monkeypatch.setattr(analytics_routes.analytics_store, "add_event", mock_add_event)

    response = client.post(
        "/api/analytics/events?event_type=api_call",
        json={"endpoint": "/api/containers", "response_time_ms": 80},
    )

    assert response.status_code == 201
    data = response.json()
    assert data == {"status": "recorded", "event_type": "api_call"}
    mock_add_event.assert_awaited_once_with(
        "api_call", {"endpoint": "/api/containers", "response_time_ms": 80}
    )


def test_record_event_validation_error(client):
    response = client.post("/api/analytics/events", json={"endpoint": "/api/deploy"})
    assert response.status_code == 422


def test_seed_sample_data_creates_events(client, monkeypatch):
    mock_add_event = AsyncMock(return_value={})
    monkeypatch.setattr(analytics_routes.analytics_store, "add_event", mock_add_event)

    response = client.post("/api/analytics/seed?days=1")

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "seeded"
    assert int(data["days"]) == 1
    assert int(data["events_created"]) > 0
    assert mock_add_event.await_count > 0


def test_seed_sample_data_validation_error(client):
    response = client.post("/api/analytics/seed?days=invalid")
    assert response.status_code == 422


def test_get_all_analytics_returns_composed_response(client, monkeypatch):
    now = datetime.now(UTC)
    mock_get_events = AsyncMock(
        return_value=[
            {
                "event_type": "api_call",
                "event_data": {"endpoint": "/api/deploy", "response_time_ms": 120},
                "created_at": now,
            },
            {
                "event_type": "llm_call",
                "event_data": {
                    "provider": "openai",
                    "model": "default",
                    "input_tokens": 100,
                    "output_tokens": 50,
                },
                "created_at": now,
            },
            {
                "event_type": "deployment",
                "event_data": {
                    "deployment_id": "dep-123",
                    "agent_id": "agent-123",
                    "agent_name": "Agent",
                    "status": "running",
                },
                "created_at": now,
            },
        ]
    )
    monkeypatch.setattr(analytics_routes.analytics_store, "get_events_since", mock_get_events)

    response = client.get("/api/analytics?days=2")

    assert response.status_code == 200
    data = response.json()
    assert "usage" in data
    assert "deployments" in data
    assert "performance" in data
    assert data["usage"]["period_days"] == 2
    assert data["deployments"]["period_days"] == 2
    assert data["performance"]["period_days"] == 2
