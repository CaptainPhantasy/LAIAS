"""
Generate Agent endpoint for Agent Generator API.

POST /api/generate-agent
Generates CrewAI agent code from natural language description.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.requests import GenerateAgentRequest
from app.models.responses import GenerateAgentResponse, ErrorResponse
from app.models.database import Agent
from app.database.session import get_db
from app.api.auth import get_current_user, DevUser
from app.services.code_generator import get_code_generator
from app.config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["generation"])


@router.post("/generate-agent", response_model=GenerateAgentResponse, status_code=status.HTTP_200_OK)
async def generate_agent(
    request: GenerateAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(get_current_user),
) -> GenerateAgentResponse:
    """
    Generate a CrewAI agent from natural language description.

    This endpoint uses LLMs to generate production-ready agent code
    following the Godzilla architectural pattern.

    - **description**: Natural language description of what the agent should do
    - **agent_name**: Valid Python class name for the generated flow
    - **complexity**: Controls number of agents and flow complexity
    - **task_type**: Optimizes generation for specific task categories
    - **tools_requested**: Optional specific tools to include
    - **llm_provider**: Choose between OpenAI and Anthropic
    - **model**: Optional specific model override

    Returns complete generated code, configuration, and validation results.
    """
    try:
        logger.info(
            "Agent generation request received",
            agent_name=request.agent_name,
            complexity=request.complexity,
            task_type=request.task_type
        )

        generator = get_code_generator()
        response = await generator.generate_agent(
            description=request.description,
            agent_name=request.agent_name,
            complexity=request.complexity,
            task_type=request.task_type,
            tools_requested=request.tools_requested,
            llm_provider=request.llm_provider,
            model=request.model,
            include_memory=request.include_memory,
            include_analytics=request.include_analytics,
            max_agents=request.max_agents
        )

        # Persist generated agent to database
        try:
            import uuid as uuid_lib
            agent_record = Agent(
                id=response.agent_id,
                name=response.agent_name,
                description=request.description,
                flow_code=response.flow_code,
                agents_yaml=response.agents_yaml,
                state_class=response.state_class,
                complexity=request.complexity,
                task_type=request.task_type,
                tools=[t.model_dump() for t in response.agents_created] if response.agents_created else [],
                requirements=response.requirements,
                llm_provider=request.llm_provider,
                model=request.model or "gpt-4o",
                estimated_cost_per_run=response.estimated_cost_per_run,
                complexity_score=response.complexity_score,
                validation_status=response.validation_status.model_dump() if response.validation_status else {},
                flow_diagram=response.flow_diagram,
                owner_id=uuid_lib.UUID(current_user.id) if current_user.id != "00000000-0000-0000-0000-000000000000" else None,
            )
            db.add(agent_record)
            await db.commit()
            logger.info("Agent persisted to database", agent_id=response.agent_id)
        except Exception as db_err:
            await db.rollback()
            logger.warning("Failed to persist agent to database (generation still returned)", error=str(db_err))

        return response

    except Exception as e:
        logger.error("Agent generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate agent: {str(e)}"
        )


@router.post("/regenerate", response_model=GenerateAgentResponse, status_code=status.HTTP_200_OK)
async def regenerate_agent(
    agent_id: str,
    feedback: str,
    previous_code: str
) -> GenerateAgentResponse:
    """
    Regenerate an agent based on feedback.

    - **agent_id**: Original agent ID
    - **feedback**: User feedback for improvement
    - **previous_code**: Previous code to improve
    """
    try:
        logger.info("Regeneration request received", agent_id=agent_id)

        generator = get_code_generator()
        response = await generator.regenerate_with_feedback(
            agent_id=agent_id,
            feedback=feedback,
            previous_code=previous_code
        )

        return response

    except Exception as e:
        logger.error("Agent regeneration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate agent: {str(e)}"
        )
