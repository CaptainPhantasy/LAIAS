from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.requests import OutputEventIngestRequest
from app.models.responses import (
    OutputEventIngestResponse,
    OutputRunDetailResponse,
    OutputRunListResponse,
)
from app.services.output_persistence import get_output_persistence_service


router = APIRouter(prefix="/api", tags=["outputs"])


@router.post(
    "/deployments/{deployment_id}/outputs/events",
    response_model=OutputEventIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest structured output event",
)
async def ingest_output_event(
    deployment_id: str,
    body: OutputEventIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> OutputEventIngestResponse:
    destinations = await get_output_persistence_service().persist_event(
        db=db,
        deployment_id=deployment_id,
        event=body,
    )

    return OutputEventIngestResponse(
        deployment_id=deployment_id,
        run_id=body.run_id,
        accepted=any(destinations.values()),
        destinations=destinations,
    )


@router.get(
    "/deployments/{deployment_id}/outputs/runs",
    response_model=OutputRunListResponse,
    summary="List persisted runs for deployment",
)
async def list_output_runs(deployment_id: str) -> OutputRunListResponse:
    runs = get_output_persistence_service().list_runs(deployment_id)
    normalized_runs = []
    for item in runs:
        event_count_raw = item.get("event_count", 0)
        event_count = event_count_raw if isinstance(event_count_raw, int) else 0
        normalized_runs.append(
            {
                "run_id": str(item.get("run_id", "")),
                "has_summary": bool(item.get("has_summary", False)),
                "has_metrics": bool(item.get("has_metrics", False)),
                "event_count": event_count,
            }
        )
    return OutputRunListResponse(deployment_id=deployment_id, runs=normalized_runs)


@router.get(
    "/deployments/{deployment_id}/outputs/runs/{run_id}",
    response_model=OutputRunDetailResponse,
    summary="Get persisted run artifacts",
)
async def get_output_run_detail(
    deployment_id: str,
    run_id: str,
) -> OutputRunDetailResponse:
    runs = get_output_persistence_service().list_runs(deployment_id)
    if not any(str(item.get("run_id", "")) == run_id for item in runs):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    detail = get_output_persistence_service().get_run_detail(deployment_id, run_id)
    metrics_value = detail.get("metrics", {})
    if not isinstance(metrics_value, dict):
        metrics_value = {}

    events_value = detail.get("events", [])
    if not isinstance(events_value, list):
        events_value = []

    return OutputRunDetailResponse(
        deployment_id=str(detail.get("deployment_id", deployment_id)),
        run_id=str(detail.get("run_id", run_id)),
        summary_markdown=str(detail.get("summary_markdown", "")),
        metrics=metrics_value,
        events=events_value,
    )
