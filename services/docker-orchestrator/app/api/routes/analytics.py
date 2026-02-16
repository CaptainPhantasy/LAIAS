"""
Analytics endpoints for LAIAS.

Provides usage statistics, deployment metrics, and performance data.
"""

from fastapi import APIRouter, status, HTTPException
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from decimal import Decimal
from collections import defaultdict
import asyncio

from app.models.responses import AnalyticsResponse, UsageStatsResponse, DeploymentStatsResponse, PerformanceMetricsResponse
from app.services.analytics_store import analytics_store

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# LLM pricing per 1K tokens (USD)
LLM_PRICING = {
    "anthropic": {
        "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-5-haiku": {"input": 0.0008, "output": 0.004},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
    },
    "openai": {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    },
    "openrouter": {
        "default": {"input": 0.001, "output": 0.002},
    },
}


def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost based on token usage."""
    provider_pricing = LLM_PRICING.get(provider.lower(), {})
    model_pricing = provider_pricing.get(model, provider_pricing.get("default", {"input": 0.001, "output": 0.002}))

    input_cost = (input_tokens / 1000) * model_pricing["input"]
    output_cost = (output_tokens / 1000) * model_pricing["output"]
    return float(input_cost + output_cost)


@router.get(
    "/usage",
    response_model=UsageStatsResponse,
    summary="Get usage statistics",
    description="Retrieve API call counts, token usage, and cost estimates",
)
async def get_usage_stats(
    days: int = 30,
    provider: Optional[str] = None,
) -> UsageStatsResponse:
    """
    Get usage statistics for the specified time period.

    Args:
        days: Number of days to look back (default: 30)
        provider: Filter by LLM provider (optional)

    Returns:
        UsageStatsResponse with aggregated usage data
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Get events from storage
    events = await analytics_store.get_events_since(since)

    # Aggregate metrics
    api_calls = defaultdict(int)
    tokens_by_provider = defaultdict(lambda: {"input": 0, "output": 0})
    daily_usage = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})

    for event in events:
        event_type = event.get("event_type")
        data = event.get("event_data", {})

        if event_type == "api_call":
            endpoint = data.get("endpoint", "unknown")
            api_calls[endpoint] += 1

        elif event_type == "llm_call":
            prov = data.get("provider", "unknown")
            model = data.get("model", "unknown")
            input_tokens = data.get("input_tokens", 0)
            output_tokens = data.get("output_tokens", 0)

            if provider is None or prov.lower() == provider.lower():
                tokens_by_provider[prov]["input"] += input_tokens
                tokens_by_provider[prov]["output"] += output_tokens

                # Calculate cost
                cost = calculate_cost(prov, model, input_tokens, output_tokens)

                # Daily aggregation
                event_date = event.get("created_at", datetime.utcnow()).date()
                daily_usage[event_date]["tokens"] += input_tokens + output_tokens
                daily_usage[event_date]["calls"] += 1
                daily_usage[event_date]["cost"] += cost

    # Calculate total cost
    total_cost = 0.0
    cost_by_provider = {}
    for prov, tokens in tokens_by_provider.items():
        cost = calculate_cost(prov, "default", tokens["input"], tokens["output"])
        cost_by_provider[prov] = round(cost, 4)
        total_cost += cost

    # Build daily timeseries
    timeseries = []
    for i in range(days):
        d = (date.today() - timedelta(days=days - i - 1))
        if d in daily_usage:
            timeseries.append({
                "date": d.isoformat(),
                "api_calls": daily_usage[d]["calls"],
                "tokens_used": daily_usage[d]["tokens"],
                "cost_usd": round(daily_usage[d]["cost"], 4),
            })
        else:
            timeseries.append({
                "date": d.isoformat(),
                "api_calls": 0,
                "tokens_used": 0,
                "cost_usd": 0.0,
            })

    total_tokens = sum(t["input"] + t["output"] for t in tokens_by_provider.values())

    return UsageStatsResponse(
        period_days=days,
        total_api_calls=sum(api_calls.values()),
        total_tokens_used=total_tokens,
        total_cost_usd=round(total_cost, 4),
        cost_by_provider=cost_by_provider,
        tokens_by_provider={
            prov: {"input": t["input"], "output": t["output"]}
            for prov, t in tokens_by_provider.items()
        },
        api_calls_by_endpoint=dict(api_calls),
        daily_timeseries=timeseries,
    )


@router.get(
    "/deployments",
    response_model=DeploymentStatsResponse,
    summary="Get deployment statistics",
    description="Retrieve deployment counts, success rates, and status distribution",
)
async def get_deployment_stats(
    days: int = 30,
) -> DeploymentStatsResponse:
    """
    Get deployment statistics for the specified time period.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        DeploymentStatsResponse with deployment metrics
    """
    since = datetime.utcnow() - timedelta(days=days)
    events = await analytics_store.get_events_since(since)

    # Aggregate deployment events
    deployments_by_status = defaultdict(int)
    deployment_events = []
    daily_deployments = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0})

    for event in events:
        event_type = event.get("event_type")
        data = event.get("event_data", {})

        if event_type == "deployment":
            status = data.get("status", "unknown")
            deployments_by_status[status] += 1

            deployment_events.append({
                "deployment_id": data.get("deployment_id"),
                "agent_id": data.get("agent_id"),
                "agent_name": data.get("agent_name"),
                "status": status,
                "created_at": event.get("created_at"),
            })

            # Daily aggregation
            event_date = event.get("created_at", datetime.utcnow()).date()
            daily_deployments[event_date]["total"] += 1
            if status == "running":
                daily_deployments[event_date]["success"] += 1
            elif status == "error":
                daily_deployments[event_date]["failed"] += 1

    total_deployments = sum(deployments_by_status.values())
    successful_deployments = deployments_by_status.get("running", 0)
    success_rate = (successful_deployments / total_deployments * 100) if total_deployments > 0 else 0

    # Build daily timeseries
    timeseries = []
    for i in range(days):
        d = (date.today() - timedelta(days=days - i - 1))
        if d in daily_deployments:
            timeseries.append({
                "date": d.isoformat(),
                "total": daily_deployments[d]["total"],
                "successful": daily_deployments[d]["success"],
                "failed": daily_deployments[d]["failed"],
                "success_rate": round(
                    (daily_deployments[d]["success"] / daily_deployments[d]["total"] * 100)
                    if daily_deployments[d]["total"] > 0 else 0,
                    2
                ),
            })
        else:
            timeseries.append({
                "date": d.isoformat(),
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
            })

    return DeploymentStatsResponse(
        period_days=days,
        total_deployments=total_deployments,
        successful_deployments=successful_deployments,
        failed_deployments=deployments_by_status.get("error", 0),
        success_rate=round(success_rate, 2),
        deployments_by_status=dict(deployments_by_status),
        daily_timeseries=timeseries,
        recent_deployments=deployment_events[-10:],  # Last 10
    )


@router.get(
    "/performance",
    response_model=PerformanceMetricsResponse,
    summary="Get performance metrics",
    description="Retrieve average response times and performance data",
)
async def get_performance_metrics(
    days: int = 7,
) -> PerformanceMetricsResponse:
    """
    Get performance metrics for the specified time period.

    Args:
        days: Number of days to look back (default: 7)

    Returns:
        PerformanceMetricsResponse with performance data
    """
    since = datetime.utcnow() - timedelta(days=days)
    events = await analytics_store.get_events_since(since)

    # Aggregate performance metrics
    response_times = []
    daily_avg_response = {}

    for event in events:
        event_type = event.get("event_type")
        data = event.get("event_data", {})

        if event_type == "api_call":
            response_time_ms = data.get("response_time_ms")
            if response_time_ms is not None:
                response_times.append(response_time_ms)

        if event_type == "api_call":
            rt = data.get("response_time_ms")
            if rt is not None:
                event_date = event.get("created_at", datetime.utcnow()).date()
                if event_date not in daily_avg_response:
                    daily_avg_response[event_date] = []
                daily_avg_response[event_date].append(rt)

    # Calculate averages
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    # Calculate daily averages
    daily_timeseries = []
    for i in range(days):
        d = (date.today() - timedelta(days=days - i - 1))
        if d in daily_avg_response:
            daily_timeseries.append({
                "date": d.isoformat(),
                "avg_response_time_ms": round(
                    sum(daily_avg_response[d]) / len(daily_avg_response[d]), 2
                ),
                "request_count": len(daily_avg_response[d]),
            })
        else:
            daily_timeseries.append({
                "date": d.isoformat(),
                "avg_response_time_ms": 0.0,
                "request_count": 0,
            })

    return PerformanceMetricsResponse(
        period_days=days,
        avg_response_time_ms=round(avg_response_time, 2),
        p50_response_time_ms=round(sorted(response_times)[len(response_times) // 2], 2) if response_times else 0,
        p95_response_time_ms=round(sorted(response_times)[int(len(response_times) * 0.95)], 2) if len(response_times) > 1 else 0,
        p99_response_time_ms=round(sorted(response_times)[int(len(response_times) * 0.99)], 2) if len(response_times) > 1 else 0,
        total_requests=len(response_times),
        daily_timeseries=daily_timeseries,
    )


@router.post(
    "/events",
    status_code=status.HTTP_201_CREATED,
    summary="Record analytics event",
    description="Record an analytics event (internal use)",
)
async def record_event(event_type: str, event_data: Dict) -> Dict[str, str]:
    """
    Record an analytics event.

    This endpoint is called internally by other services to track events.

    Event types:
    - api_call: Tracks API endpoint usage
    - llm_call: Tracks LLM token usage
    - deployment: Tracks agent deployments

    Args:
        event_type: Type of event (api_call, llm_call, deployment)
        event_data: Event-specific data

    Returns:
        Confirmation message
    """
    await analytics_store.add_event(event_type, event_data)

    return {"status": "recorded", "event_type": event_type}


@router.post(
    "/seed",
    status_code=status.HTTP_201_CREATED,
    summary="Seed sample analytics data",
    description="Generate sample analytics data for testing (development only)",
)
async def seed_sample_data(days: int = 30) -> Dict[str, str]:
    """
    Seed the analytics store with sample data.

    This is a convenience endpoint for development/testing.
    In production, analytics are populated by actual usage.

    Args:
        days: Number of days of historical data to generate

    Returns:
        Confirmation message with counts
    """
    from random import randint, choices
    from datetime import timedelta

    LLM_PROVIDERS = ["anthropic", "openai", "openrouter"]
    API_ENDPOINTS = [
        "/api/generate",
        "/api/deploy",
        "/api/containers",
        "/api/health",
    ]

    now = datetime.utcnow()
    events_created = 0

    # Generate data for each day
    for day_offset in range(days, 0, -1):
        date = now - timedelta(days=day_offset)

        # API calls
        for _ in range(randint(10, 50)):
            call_time = date + timedelta(
                hours=randint(0, 23),
                minutes=randint(0, 59),
            )
            await analytics_store.add_event("api_call", {
                "endpoint": choices(API_ENDPOINTS, weights=[40, 20, 20, 20])[0],
                "response_time_ms": randint(50, 500),
            })
            events_created += 1

        # LLM calls
        for _ in range(randint(5, 20)):
            llm_time = date + timedelta(
                hours=randint(0, 23),
                minutes=randint(0, 59),
            )
            provider = choices(LLM_PROVIDERS, weights=[50, 35, 15])[0]

            await analytics_store.add_event("llm_call", {
                "provider": provider,
                "model": f"{provider}-model",
                "input_tokens": randint(100, 5000),
                "output_tokens": randint(50, 2000),
            })
            events_created += 1

        # Deployments
        for _ in range(randint(1, 5)):
            deploy_time = date + timedelta(
                hours=randint(0, 23),
                minutes=randint(0, 59),
            )
            status = "running" if randint(1, 100) <= 85 else "error"

            await analytics_store.add_event("deployment", {
                "deployment_id": f"seed-{deploy_time.strftime('%Y%m%d-%H%M%S')}",
                "agent_id": f"agent-{randint(1000, 9999)}",
                "agent_name": f"Seed Agent {randint(1, 100)}",
                "status": status,
            })
            events_created += 1

    return {
        "status": "seeded",
        "events_created": str(events_created),
        "days": str(days),
    }


@router.get(
    "",
    response_model=AnalyticsResponse,
    summary="Get all analytics",
    description="Get comprehensive analytics overview",
)
async def get_all_analytics(days: int = 30) -> AnalyticsResponse:
    """
    Get all analytics data in a single response.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        AnalyticsResponse with all metrics
    """
    usage = await get_usage_stats(days=days)
    deployments = await get_deployment_stats(days=days)
    performance = await get_performance_metrics(days=min(days, 7))

    return AnalyticsResponse(
        usage=usage,
        deployments=deployments,
        performance=performance,
    )
