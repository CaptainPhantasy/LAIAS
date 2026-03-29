"""
DASES Pipeline endpoints for Agent Generator API.

POST /api/dases/run        — Start a DASES pipeline run
GET  /api/dases/status/:id — Get pipeline status
GET  /api/dases/artifacts/:id — Get pipeline artifacts
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Optional

from app.api.auth import DevUser, get_current_user
from app.middleware.rate_limit import RATE_LIMITS, limiter

logger = structlog.get_logger()

router = APIRouter(prefix="/api/dases", tags=["dases"])


# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================

class DASESRunRequest(BaseModel):
    """Request to start a DASES pipeline run."""
    project_name: str = Field(..., description="Name of the project to build")
    project_description: str = Field(
        ...,
        description="Detailed project requirements",
        min_length=20,
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="Override LLM model (default: glm-4-flash via ZAI)"
    )
    max_retries: int = Field(default=3, ge=1, le=5, description="Max critic retries per gate")
    verbose: bool = Field(default=True, description="Enable verbose agent output")


class DASESStatusResponse(BaseModel):
    """Pipeline status response."""
    task_id: str
    project_name: str
    status: str
    phase: str
    current_agent: str
    progress: float
    quality_gates: list[dict]
    error_count: int
    last_error: Optional[str] = None


class DASESRunResponse(BaseModel):
    """Response after starting a pipeline run."""
    task_id: str
    status: str
    message: str


# =============================================================================
# IN-MEMORY PIPELINE REGISTRY (lightweight — no DB schema changes)
# =============================================================================

_pipeline_runs: dict[str, dict] = {}


# =============================================================================
# ENDPOINTS
# =============================================================================

@limiter.limit(RATE_LIMITS.get("generation", "10/minute"))
@router.post("/run", response_model=DASESRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_dases_pipeline(
    request: Request,
    body: DASESRunRequest,
    current_user: DevUser = Depends(get_current_user),
) -> DASESRunResponse:
    """
    Start a DASES pipeline run.

    Launches the full 8-agent quality-gated pipeline to produce
    production-release quality software from the given requirements.

    The pipeline runs asynchronously. Use GET /api/dases/status/{task_id}
    to check progress.
    """
    import asyncio
    from datetime import datetime

    logger.info(
        "DASES pipeline run requested",
        project_name=body.project_name,
        user=current_user.id,
    )

    task_id = f"dases_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Store initial state
    _pipeline_runs[task_id] = {
        "task_id": task_id,
        "project_name": body.project_name,
        "status": "queued",
        "phase": "INIT",
        "current_agent": "PLANNER",
        "progress": 0.0,
        "quality_gates": [],
        "error_count": 0,
        "last_error": None,
        "artifacts": {},
    }

    # Launch pipeline in background
    asyncio.create_task(_execute_pipeline(task_id, body))

    return DASESRunResponse(
        task_id=task_id,
        status="queued",
        message=f"DASES pipeline started for '{body.project_name}'. "
                f"Track progress at GET /api/dases/status/{task_id}",
    )


@router.get("/status/{task_id}", response_model=DASESStatusResponse)
async def get_pipeline_status(
    task_id: str,
    current_user: DevUser = Depends(get_current_user),
) -> DASESStatusResponse:
    """Get the current status of a DASES pipeline run."""
    run = _pipeline_runs.get(task_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run '{task_id}' not found",
        )
    return DASESStatusResponse(**{k: v for k, v in run.items() if k != "artifacts"})


@router.get("/artifacts/{task_id}")
async def get_pipeline_artifacts(
    task_id: str,
    current_user: DevUser = Depends(get_current_user),
) -> dict:
    """Get all artifacts produced by a DASES pipeline run."""
    run = _pipeline_runs.get(task_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run '{task_id}' not found",
        )
    return {
        "task_id": task_id,
        "status": run["status"],
        "artifacts": run.get("artifacts", {}),
    }


@router.get("/runs")
async def list_pipeline_runs(
    current_user: DevUser = Depends(get_current_user),
) -> list[dict]:
    """List all DASES pipeline runs."""
    return [
        {
            "task_id": r["task_id"],
            "project_name": r["project_name"],
            "status": r["status"],
            "phase": r["phase"],
            "progress": r["progress"],
        }
        for r in _pipeline_runs.values()
    ]


# =============================================================================
# BACKGROUND EXECUTION
# =============================================================================

async def _execute_pipeline(task_id: str, body: DASESRunRequest) -> None:
    """Execute the DASES pipeline in the background."""
    import asyncio

    try:
        _pipeline_runs[task_id]["status"] = "running"

        # Import here to avoid circular imports and keep route file lightweight
        from agents.dases_pipeline.state import DASESConfig
        from agents.dases_pipeline.flow import DASESFlow

        config = DASESConfig(
            max_retries=body.max_retries,
            verbose=body.verbose,
        )
        if body.llm_model:
            config.default_model = body.llm_model

        flow = DASESFlow(config=config)

        # Run in executor since CrewAI kickoff is synchronous
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: flow.kickoff(inputs={
                "project_name": body.project_name,
                "project_description": body.project_description,
                "inputs": {
                    "name": body.project_name,
                    "description": body.project_description,
                },
            }),
        )

        # Update registry with final state
        state = flow.state
        _pipeline_runs[task_id].update({
            "status": state.status,
            "phase": state.phase.value if hasattr(state.phase, "value") else str(state.phase),
            "current_agent": state.current_agent.value if hasattr(state.current_agent, "value") else str(state.current_agent),
            "progress": state.progress,
            "quality_gates": [
                {
                    "gate": g.gate_number,
                    "name": g.name,
                    "status": g.status.value,
                    "attempts": g.attempts,
                }
                for g in state.quality_gates
            ],
            "error_count": state.error_count,
            "last_error": state.last_error,
            "artifacts": state.artifacts,
        })

        logger.info(
            "DASES pipeline completed",
            task_id=task_id,
            status=state.status,
            progress=state.progress,
        )

    except Exception as e:
        logger.error("DASES pipeline failed", task_id=task_id, error=str(e))
        _pipeline_runs[task_id].update({
            "status": "error",
            "last_error": str(e),
            "error_count": _pipeline_runs[task_id].get("error_count", 0) + 1,
        })
