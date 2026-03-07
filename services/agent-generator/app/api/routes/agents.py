"""
Agents CRUD endpoint for Agent Generator API.

CRUD operations for saved agents.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import DevUser, get_current_user
from app.database.session import get_db
from app.models.database import Agent, AgentVersion
from app.models.requests import AgentUpdateRequest
from app.models.responses import (
    AgentDetailResponse,
    AgentListResponse,
    AgentRollbackResponse,
    AgentVersionListResponse,
    AgentVersionResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/agents", response_model=AgentListResponse, status_code=status.HTTP_200_OK)
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: DevUser = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    task_type: str | None = Query(None),
    complexity: str | None = Query(None),
    search: str | None = Query(None),
    team_id: str | None = Query(None),
) -> AgentListResponse:
    """
    List saved agents with optional filtering.

    Query parameters:
    - **limit**: Maximum results to return (default: 50, max: 200)
    - **offset**: Results offset for pagination (default: 0)
    - **task_type**: Filter by task type
    - **complexity**: Filter by complexity
    - **search**: Search in description and name
    - **team_id**: Filter by team ID (only agents shared with this team)
    """
    try:
        # Build base query
        query = select(Agent)

        # Apply filters
        conditions = []

        # Filter by user's own agents or team-shared agents
        user_uuid = current_user.id
        from sqlalchemy import UUID, cast

        user_filter = or_(
            Agent.owner_id == cast(user_uuid, UUID),
            Agent.team_id.is_(None),  # Public agents
        )

        # If team_id specified, also include agents from that team
        if team_id:
            try:
                import uuid as uuid_lib

                team_uuid = uuid_lib.UUID(team_id)
                user_filter = or_(user_filter, Agent.team_id == team_uuid)
            except ValueError:
                pass  # Invalid team_id, ignore

        conditions.append(user_filter)

        if task_type:
            conditions.append(Agent.task_type == task_type)
        if complexity:
            conditions.append(Agent.complexity == complexity)
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(Agent.name.ilike(search_pattern), Agent.description.ilike(search_pattern))
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Agent.created_at.desc()).offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        agents = result.scalars().all()

        # Convert to response format
        agents_list = [agent.to_dict() for agent in agents]

        return AgentListResponse(agents=agents_list, total=total, limit=limit, offset=offset)

    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}",
        )


@router.get(
    "/agents/{agent_id}", response_model=AgentDetailResponse, status_code=status.HTTP_200_OK
)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)) -> AgentDetailResponse:
    """
    Get a saved agent by ID.

    Path parameters:
    - **agent_id**: Unique agent identifier
    """
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    agent_dict = agent.to_dict()
    return AgentDetailResponse(**agent_dict)


@router.get(
    "/agents/{agent_id}/versions",
    response_model=AgentVersionListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_agent_versions(
    agent_id: str, db: AsyncSession = Depends(get_db)
) -> AgentVersionListResponse:
    agent_query = select(Agent).where(Agent.id == agent_id)
    agent_result = await db.execute(agent_query)
    agent = agent_result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    versions_query = (
        select(AgentVersion)
        .where(AgentVersion.agent_id == agent_id)
        .order_by(AgentVersion.version.desc())
    )
    versions_result = await db.execute(versions_query)
    historical_versions = versions_result.scalars().all()

    response_versions = [
        AgentVersionResponse(**version_record.to_dict(), is_current=False)
        for version_record in historical_versions
        if version_record.version != agent.version
    ]

    response_versions.append(
        AgentVersionResponse(
            id=None,
            agent_id=agent.id,
            version=agent.version,
            flow_code=agent.flow_code,
            agents_yaml=agent.agents_yaml,
            state_class=agent.state_class,
            requirements=agent.requirements or [],
            validation_status=agent.validation_status or {},
            flow_diagram=agent.flow_diagram,
            created_at=agent.updated_at,
            change_summary="Current active version",
            is_current=True,
        )
    )
    response_versions.sort(key=lambda record: record.version, reverse=True)

    return AgentVersionListResponse(
        agent_id=agent.id,
        current_version=agent.version,
        latest_version=agent.latest_version,
        versions=response_versions,
    )


@router.get(
    "/agents/{agent_id}/versions/{version}",
    response_model=AgentVersionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_agent_version(
    agent_id: str, version: int, db: AsyncSession = Depends(get_db)
) -> AgentVersionResponse:
    agent_query = select(Agent).where(Agent.id == agent_id)
    agent_result = await db.execute(agent_query)
    agent = agent_result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    if version == agent.version:
        return AgentVersionResponse(
            id=None,
            agent_id=agent.id,
            version=agent.version,
            flow_code=agent.flow_code,
            agents_yaml=agent.agents_yaml,
            state_class=agent.state_class,
            requirements=agent.requirements or [],
            validation_status=agent.validation_status or {},
            flow_diagram=agent.flow_diagram,
            created_at=agent.updated_at,
            change_summary="Current active version",
            is_current=True,
        )

    version_query = select(AgentVersion).where(
        AgentVersion.agent_id == agent_id,
        AgentVersion.version == version,
    )
    version_result = await db.execute(version_query)
    version_record = version_result.scalar_one_or_none()

    if not version_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found for agent {agent_id}",
        )

    return AgentVersionResponse(**version_record.to_dict(), is_current=False)


@router.post(
    "/agents/{agent_id}/versions/{version}/rollback",
    response_model=AgentRollbackResponse,
    status_code=status.HTTP_200_OK,
)
async def rollback_agent_version(
    agent_id: str, version: int, db: AsyncSession = Depends(get_db)
) -> AgentRollbackResponse:
    agent_query = select(Agent).where(Agent.id == agent_id)
    agent_result = await db.execute(agent_query)
    agent = agent_result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    if version == agent.version:
        return AgentRollbackResponse(
            agent_id=agent.id,
            from_version=agent.version,
            rolled_back_to_version=version,
            new_version=agent.version,
        )

    version_query = select(AgentVersion).where(
        AgentVersion.agent_id == agent_id,
        AgentVersion.version == version,
    )
    version_result = await db.execute(version_query)
    target_version = version_result.scalar_one_or_none()

    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found for agent {agent_id}",
        )

    current_snapshot_query = select(AgentVersion).where(
        AgentVersion.agent_id == agent.id,
        AgentVersion.version == agent.version,
    )
    current_snapshot_result = await db.execute(current_snapshot_query)
    current_snapshot = current_snapshot_result.scalar_one_or_none()
    if not current_snapshot:
        db.add(
            AgentVersion(
                agent_id=agent.id,
                version=agent.version,
                flow_code=agent.flow_code,
                agents_yaml=agent.agents_yaml,
                state_class=agent.state_class,
                requirements=agent.requirements or [],
                validation_status=agent.validation_status or {},
                flow_diagram=agent.flow_diagram,
                change_summary=f"Saved before rollback to version {version}",
            )
        )

    previous_version = agent.version
    next_version = max(agent.latest_version, agent.version) + 1

    agent.flow_code = target_version.flow_code or ""
    agent.agents_yaml = target_version.agents_yaml
    agent.state_class = target_version.state_class
    agent.requirements = target_version.requirements or []
    agent.validation_status = target_version.validation_status or {}
    agent.flow_diagram = target_version.flow_diagram
    agent.version = next_version
    agent.latest_version = next_version
    agent.updated_at = datetime.now(UTC)

    await db.commit()

    logger.info(
        "Agent rolled back to historical version",
        agent_id=agent_id,
        from_version=previous_version,
        restored_version=version,
        new_version=next_version,
    )

    return AgentRollbackResponse(
        agent_id=agent.id,
        from_version=previous_version,
        rolled_back_to_version=version,
        new_version=next_version,
    )


@router.put("/agents/{agent_id}", status_code=status.HTTP_200_OK)
async def update_agent(
    agent_id: str, request: AgentUpdateRequest, db: AsyncSession = Depends(get_db)
):
    """
    Update a saved agent.

    Path parameters:
    - **agent_id**: Unique agent identifier

    Request body:
    - **description**: Updated description
    - **is_active**: Whether agent is active
    - **tags**: Updated tags
    - **version_notes**: Notes about this version
    """
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    # Update fields if provided
    if request.description is not None:
        agent.description = request.description
    if request.is_active is not None:
        agent.is_active = request.is_active
    if request.tags is not None:
        requirements_data: dict[str, Any] = {}
        if isinstance(agent.requirements, dict):
            requirements_data.update(agent.requirements)
        elif isinstance(agent.requirements, list):
            requirements_data["packages"] = agent.requirements
        requirements_data["tags"] = request.tags
        agent.requirements = requirements_data
    if request.version_notes is not None:
        requirements_data: dict[str, Any] = {}
        if isinstance(agent.requirements, dict):
            requirements_data.update(agent.requirements)
        elif isinstance(agent.requirements, list):
            requirements_data["packages"] = agent.requirements
        requirements_data["version_notes"] = request.version_notes
        agent.requirements = requirements_data

    agent.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(agent)

    logger.info("Agent updated", agent_id=agent_id)
    return agent.to_dict()


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a saved agent.

    Path parameters:
    - **agent_id**: Unique agent identifier
    """
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    await db.delete(agent)
    await db.commit()

    logger.info("Agent deleted", agent_id=agent_id)

    return None


@router.post("/agents/{agent_id}/share", status_code=status.HTTP_200_OK)
async def share_agent_with_team(
    agent_id: str,
    team_id: str,
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Share an agent with a team.

    Only the agent owner can share it.
    Path parameters:
    - **agent_id**: Unique agent identifier
    Request body:
    - **team_id**: Team ID to share with (as query param or body)
    """
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    # Verify ownership
    from sqlalchemy import UUID, cast

    if agent.owner_id != cast(current_user.id, UUID):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the agent owner can share it"
        )

    # Verify team exists and user is a member
    try:
        import uuid as uuid_lib

        team_uuid = uuid_lib.UUID(team_id)
        user_uuid = uuid_lib.UUID(current_user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid team ID format"
        )

    from app.models.team import TeamMember

    team_result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_uuid, TeamMember.user_id == user_uuid)
    )
    if not team_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this team"
        )

    # Share agent with team
    agent.team_id = team_uuid
    await db.commit()

    logger.info("Agent shared with team", agent_id=agent_id, team_id=team_id)

    return agent.to_dict()


@router.delete("/agents/{agent_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_agent_from_team(
    agent_id: str,
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Unshare an agent from any team (make it private).

    Only the agent owner can unshare it.
    """
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    # Verify ownership
    from sqlalchemy import UUID, cast

    if agent.owner_id != cast(current_user.id, UUID):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the agent owner can unshare it"
        )

    # Unshare from team
    agent.team_id = None
    await db.commit()

    logger.info("Agent unshared from team", agent_id=agent_id)

    return None
