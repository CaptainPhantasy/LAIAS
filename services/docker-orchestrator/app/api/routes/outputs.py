from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.requests import OutputEventIngestRequest
from app.models.responses import OutputEventIngestResponse
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
