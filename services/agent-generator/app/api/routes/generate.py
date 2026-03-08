"""
Generate Agent endpoint for Agent Generator API.

POST /api/generate-agent
Generates CrewAI agent code from natural language description.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import DevUser, get_current_user
from app.database.session import get_db
from app.middleware.rate_limit import RATE_LIMITS, limiter
from app.models.database import Agent, AgentVersion
from app.models.requests import GenerateAgentRequest
from app.models.responses import GenerateAgentResponse
from app.services.code_generator import get_code_generator
from app.services.llm_service import get_llm_service

logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["generation"])


class GenerateAndDeployRequest(GenerateAgentRequest):
    output_config: dict[str, bool] | None = None
    output_path: str | None = None
    output_format: str = "markdown"
    input_volumes: list[dict[str, str]] | None = None


@limiter.limit(RATE_LIMITS["generation"])
@router.post(
    "/generate-agent", response_model=GenerateAgentResponse, status_code=status.HTTP_200_OK
)
async def generate_agent(
    request: Request,
    body: GenerateAgentRequest,
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
            agent_name=body.agent_name,
            complexity=body.complexity,
            task_type=body.task_type,
        )

        generator = get_code_generator()
        response = await generator.generate_agent(
            description=body.description,
            agent_name=body.agent_name,
            complexity=body.complexity,
            task_type=body.task_type,
            tools_requested=body.tools_requested,
            llm_provider=body.llm_provider,
            model=body.model,
            include_memory=body.include_memory,
            include_analytics=body.include_analytics,
            max_agents=body.max_agents,
        )

        # Persist generated agent to database
        try:
            import uuid as uuid_lib

            owner_id = (
                uuid_lib.UUID(current_user.id)
                if current_user.id != "00000000-0000-0000-0000-000000000000"
                else None
            )
            query = select(Agent).where(Agent.id == response.agent_id)
            result = await db.execute(query)
            existing_agent = result.scalar_one_or_none()

            if existing_agent:
                db.add(
                    AgentVersion(
                        agent_id=existing_agent.id,
                        version=existing_agent.version,
                        flow_code=existing_agent.flow_code,
                        agents_yaml=existing_agent.agents_yaml,
                        state_class=existing_agent.state_class,
                        requirements=existing_agent.requirements or [],
                        validation_status=existing_agent.validation_status or {},
                        flow_diagram=existing_agent.flow_diagram,
                        change_summary="Previous version saved before regeneration",
                    )
                )
                next_version = max(existing_agent.latest_version, existing_agent.version) + 1
                existing_agent.name = response.agent_name
                existing_agent.description = body.description
                existing_agent.flow_code = response.flow_code
                existing_agent.agents_yaml = response.agents_yaml
                existing_agent.state_class = response.state_class
                existing_agent.complexity = body.complexity
                existing_agent.task_type = body.task_type
                existing_agent.tools = (
                    [t.model_dump() for t in response.agents_created]
                    if response.agents_created
                    else []
                )
                existing_agent.requirements = response.requirements
                existing_agent.llm_provider = body.llm_provider
                existing_agent.model = (
                    body.model
                    if body.model and body.model.lower() != "default"
                    else get_llm_service()._get_model_for_provider(body.llm_provider)
                )
                existing_agent.estimated_cost_per_run = response.estimated_cost_per_run
                existing_agent.complexity_score = response.complexity_score
                existing_agent.validation_status = (
                    response.validation_status.model_dump() if response.validation_status else {}
                )
                existing_agent.flow_diagram = response.flow_diagram
                if existing_agent.owner_id is None:
                    existing_agent.owner_id = owner_id
                existing_agent.version = next_version
                existing_agent.latest_version = next_version
            else:
                agent_record = Agent(
                    id=response.agent_id,
                    name=response.agent_name,
                    description=body.description,
                    flow_code=response.flow_code,
                    agents_yaml=response.agents_yaml,
                    state_class=response.state_class,
                    complexity=body.complexity,
                    task_type=body.task_type,
                    tools=[t.model_dump() for t in response.agents_created]
                    if response.agents_created
                    else [],
                    requirements=response.requirements,
                    llm_provider=body.llm_provider,
                    model=body.model
                    if body.model and body.model.lower() != "default"
                    else get_llm_service()._get_model_for_provider(body.llm_provider),
                    estimated_cost_per_run=response.estimated_cost_per_run,
                    complexity_score=response.complexity_score,
                    validation_status=response.validation_status.model_dump()
                    if response.validation_status
                    else {},
                    flow_diagram=response.flow_diagram,
                    owner_id=owner_id,
                    version=1,
                    latest_version=1,
                )
                db.add(agent_record)

            await db.commit()
            logger.info("Agent persisted to database", agent_id=response.agent_id)
        except Exception as db_err:
            await db.rollback()
            logger.warning(
                "Failed to persist agent to database (generation still returned)", error=str(db_err)
            )

        return response

    except Exception as e:
        logger.error("Agent generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate agent: {str(e)}",
        )


@limiter.limit(RATE_LIMITS["generation"])
@router.post("/generate-and-deploy", status_code=status.HTTP_201_CREATED)
async def generate_and_deploy(
    request: Request,
    body: GenerateAndDeployRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(get_current_user),
):
    """
    Generate an agent and immediately deploy it to a Docker container.

    Single-call server-side handoff: Generator → DB save → Orchestrator deploy.
    Eliminates the need for the frontend to bridge two services.

    Returns both the generated code and deployment details.
    """
    # Step 1: Generate using the code generator directly
    generator = get_code_generator()
    response = await generator.generate_agent(
        description=body.description,
        agent_name=body.agent_name,
        complexity=body.complexity,
        task_type=body.task_type,
        tools_requested=body.tools_requested,
        llm_provider=body.llm_provider,
        model=body.model,
    )

    # Persist to database
    try:
        from datetime import UTC, datetime

        agent_record = Agent(
            id=response.agent_id,
            name=response.agent_name,
            description=body.description,
            flow_code=response.flow_code,
            agents_yaml=response.agents_yaml,
            requirements=response.requirements,
            owner_id=current_user.id,
            created_at=datetime.now(UTC),
        )
        db.add(agent_record)
        await db.commit()
        logger.info("Agent persisted to DB", agent_id=response.agent_id)
    except Exception as db_err:
        logger.warning(
            "Failed to persist agent to database (generation still returned)", error=str(db_err)
        )

    # Step 2: Deploy via internal HTTP to Docker Orchestrator
    from app.services.orchestrator_client import OrchestratorError, get_orchestrator_client

    try:
        deployment = await get_orchestrator_client().deploy_agent(
            agent_id=response.agent_id,
            agent_name=response.agent_name,
            flow_code=response.flow_code,
            agents_yaml=response.agents_yaml,
            requirements=response.requirements,
            output_config=body.output_config,
            output_path=body.output_path,
            output_format=body.output_format,
            input_volumes=body.input_volumes,
            auto_start=True,
        )

        # Update deployed_count in DB
        try:
            from sqlalchemy import select as sa_select

            query = sa_select(Agent).where(Agent.id == response.agent_id)
            result = await db.execute(query)
            agent_record = result.scalar_one_or_none()
            if agent_record:
                agent_record.deployed_count = (agent_record.deployed_count or 0) + 1
                from datetime import UTC, datetime

                agent_record.last_deployed = datetime.now(UTC)
                await db.commit()
        except Exception as e:
            logger.debug(
                "Failed to update deployed_count (non-fatal)",
                agent_id=response.agent_id,
                error=str(e),
                context="generate_and_deploy",
            )

        logger.info(
            "Generate-and-deploy complete",
            agent_id=response.agent_id,
            deployment_id=deployment.get("deployment_id"),
        )

        return {
            "generation": response.model_dump(),
            "deployment": deployment,
        }

    except OrchestratorError as e:
        logger.error("Deploy handoff failed", agent_id=response.agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent generated successfully but deployment failed: {str(e)}",
        )
    except Exception as e:
        logger.error("Deploy handoff failed (unexpected)", agent_id=response.agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent generated but orchestrator unreachable: {str(e)}",
        )


class DeployProxyRequest(BaseModel):
    agent_id: str
    agent_name: str
    flow_code: str
    agents_yaml: str = ""
    auto_start: bool = True
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    output_config: dict[str, bool] = {"postgres": True, "files": True}
    output_path: str | None = None
    output_format: str = "markdown"


@limiter.limit(RATE_LIMITS["deployment"])
@router.post("/deploy", status_code=status.HTTP_201_CREATED)
async def deploy_agent_proxy(request: Request, body: DeployProxyRequest):
    """
    Proxy deploy endpoint — forwards to Docker Orchestrator.

    Allows the frontend to deploy through a single service (agent-generator)
    instead of needing direct access to the orchestrator.
    """
    from app.services.orchestrator_client import OrchestratorError, get_orchestrator_client

    try:
        deployment = await get_orchestrator_client().deploy_agent(
            agent_id=body.agent_id,
            agent_name=body.agent_name,
            flow_code=body.flow_code,
            agents_yaml=body.agents_yaml,
            output_config=body.output_config,
            output_path=body.output_path,
            output_format=body.output_format,
            auto_start=body.auto_start,
            memory_limit=body.memory_limit,
            cpu_limit=body.cpu_limit,
        )
        return deployment
    except OrchestratorError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Orchestrator unreachable: {str(e)}",
        )


@limiter.limit(RATE_LIMITS["generation"])
@router.post("/regenerate", response_model=GenerateAgentResponse, status_code=status.HTTP_200_OK)
async def regenerate_agent(
    request: Request,
    agent_id: str,
    feedback: str,
    previous_code: str,
    db: AsyncSession = Depends(get_db),
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
            agent_id=agent_id, feedback=feedback, previous_code=previous_code
        )

        query = select(Agent).where(Agent.id == agent_id)
        result = await db.execute(query)
        agent_record = result.scalar_one_or_none()
        if not agent_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        db.add(
            AgentVersion(
                agent_id=agent_record.id,
                version=agent_record.version,
                flow_code=agent_record.flow_code,
                agents_yaml=agent_record.agents_yaml,
                state_class=agent_record.state_class,
                requirements=agent_record.requirements or [],
                validation_status=agent_record.validation_status or {},
                flow_diagram=agent_record.flow_diagram,
                change_summary=feedback,
            )
        )

        next_version = max(agent_record.latest_version, agent_record.version) + 1
        agent_record.flow_code = response.flow_code
        agent_record.agents_yaml = response.agents_yaml
        agent_record.state_class = response.state_class
        agent_record.requirements = response.requirements
        agent_record.validation_status = (
            response.validation_status.model_dump() if response.validation_status else {}
        )
        agent_record.flow_diagram = response.flow_diagram
        agent_record.estimated_cost_per_run = response.estimated_cost_per_run
        agent_record.complexity_score = response.complexity_score
        agent_record.version = next_version
        agent_record.latest_version = next_version
        await db.commit()

        return response

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Agent regeneration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate agent: {str(e)}",
        )
