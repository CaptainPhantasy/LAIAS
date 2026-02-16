"""
Team API Routes.

Team management with RBAC - create, list, update, delete teams and members.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.api.auth import (
    get_current_user, DevUser,
    verify_team_ownership, verify_team_ownership_or_admin,
    require_admin_or_owner
)
from app.models.team import Team, TeamMember, User

router = APIRouter(prefix="/api/teams", tags=["teams"])


# =============================================================================
# Schemas
# =============================================================================

class TeamCreate(BaseModel):
    """Create team request."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)


class TeamUpdate(BaseModel):
    """Update team request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class TeamMemberResponse(BaseModel):
    """Team member response."""
    user_id: str
    email: str
    name: Optional[str] = None
    role: str
    joined_at: str


class TeamResponse(BaseModel):
    """Team response."""
    id: str
    name: str
    slug: str
    owner_id: Optional[str] = None
    created_at: str
    members_count: int = 0

    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    """Team detail with members."""
    members: List[TeamMemberResponse] = []


class AddMemberRequest(BaseModel):
    """Add team member request."""
    user_id: str
    role: str = Field(default="member", pattern="^(owner|admin|member|viewer)$")


class UpdateMemberRoleRequest(BaseModel):
    """Update member role request."""
    role: str = Field(..., pattern="^(owner|admin|member|viewer)$")


# =============================================================================
# Helpers
# =============================================================================

def _slugify(name: str) -> str:
    """Convert name to URL-safe slug."""
    slug = name.lower().replace(" ", "-")
    return "".join(c for c in slug if c.isalnum() or c == "-")


async def _get_members_with_users(team_id: uuid.UUID, db: AsyncSession) -> List[dict]:
    """
    Get team members with actual user data from users table.

    Returns list of dicts with user_id, email, name, role, joined_at.
    """
    # Join team_members with users table
    result = await db.execute(
        select(TeamMember, User)
        .join(User, TeamMember.user_id == User.id)
        .where(TeamMember.team_id == team_id)
    )
    rows = result.all()

    return [
        {
            "user_id": str(member.user_id),
            "email": user.email,
            "name": user.name,
            "role": member.role,
            "joined_at": member.joined_at.isoformat()
        }
        for member, user in rows
    ]


# =============================================================================
# Routes
# =============================================================================

@router.get("", response_model=List[TeamResponse])
async def list_teams(
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[TeamResponse]:
    """
    List all teams the current user is a member of.
    """
    user_uuid = uuid.UUID(current_user.id)

    # Query teams where user is a member
    result = await db.execute(
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_uuid)
        .order_by(Team.created_at.desc())
    )
    teams = result.scalars().all()

    # Get member counts
    responses = []
    for team in teams:
        count_result = await db.execute(
            select(TeamMember).where(TeamMember.team_id == team.id)
        )
        responses.append(TeamResponse(
            id=str(team.id),
            name=team.name,
            slug=team.slug,
            owner_id=str(team.owner_id) if team.owner_id else None,
            created_at=team.created_at.isoformat(),
            members_count=len(count_result.scalars().all())
        ))

    return responses


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team: TeamCreate,
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamResponse:
    """
    Create a new team. User becomes owner.
    """
    slug = team.slug or _slugify(team.name)

    # Check slug uniqueness
    existing = await db.execute(
        select(Team).where(Team.slug == slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Team with slug '{slug}' already exists"
        )

    user_uuid = uuid.UUID(current_user.id)

    # Create team
    new_team = Team(
        name=team.name,
        slug=slug,
        owner_id=user_uuid
    )
    db.add(new_team)
    await db.flush()

    # Add owner as member
    member = TeamMember(
        team_id=new_team.id,
        user_id=user_uuid,
        role="owner"
    )
    db.add(member)
    await db.commit()

    return TeamResponse(
        id=str(new_team.id),
        name=new_team.name,
        slug=new_team.slug,
        owner_id=str(new_team.owner_id),
        created_at=new_team.created_at.isoformat(),
        members_count=1
    )


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: str,
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamDetailResponse:
    """
    Get team details with member list.

    User must be a member of the team.
    """
    try:
        team_uuid = uuid.UUID(team_id)
        user_uuid = uuid.UUID(current_user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid team ID"
        )

    # Get team
    result = await db.execute(
        select(Team).where(Team.id == team_uuid)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Verify user is a member
    member_check = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_uuid,
            TeamMember.user_id == user_uuid
        )
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )

    # Get members with user data
    members_data = await _get_members_with_users(team.id, db)

    member_responses = [
        TeamMemberResponse(**m) for m in members_data
    ]

    return TeamDetailResponse(
        id=str(team.id),
        name=team.name,
        slug=team.slug,
        owner_id=str(team.owner_id) if team.owner_id else None,
        created_at=team.created_at.isoformat(),
        members_count=len(member_responses),
        members=member_responses
    )


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    update: TeamUpdate,
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamResponse:
    """
    Update team name. Only owner/admin can update.
    """
    # Verify ownership or admin
    team, user_role = await verify_team_ownership_or_admin(
        team_id, current_user, db
    )

    if update.name:
        team.name = update.name

    await db.commit()
    await db.refresh(team)

    count_result = await db.execute(select(TeamMember).where(TeamMember.team_id == team.id))

    return TeamResponse(
        id=str(team.id),
        name=team.name,
        slug=team.slug,
        owner_id=str(team.owner_id) if team.owner_id else None,
        created_at=team.created_at.isoformat(),
        members_count=len(count_result.scalars().all())
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a team. Only owner can delete.
    """
    # Verify ownership
    team = await verify_team_ownership(team_id, current_user, db)

    await db.delete(team)
    await db.commit()


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: str,
    request: AddMemberRequest,
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamMemberResponse:
    """
    Add a member to the team. Owner/admin only.
    """
    # Verify ownership or admin
    team, user_role = await verify_team_ownership_or_admin(
        team_id, current_user, db
    )

    try:
        user_uuid = uuid.UUID(request.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    # Verify user exists
    user_result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already member
    existing = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == user_uuid
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a team member"
        )

    # Add member
    member = TeamMember(
        team_id=team.id,
        user_id=user_uuid,
        role=request.role
    )
    db.add(member)
    await db.commit()

    # Get user data for response
    user_data = await db.execute(select(User).where(User.id == user_uuid))
    user = user_data.scalar_one()

    return TeamMemberResponse(
        user_id=request.user_id,
        email=user.email,
        name=user.name,
        role=request.role,
        joined_at=member.joined_at.isoformat()
    )


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Remove a member from the team. Owner/admin only.

    Owner cannot remove themselves.
    """
    try:
        target_user_uuid = uuid.UUID(user_id)
        requester_uuid = uuid.UUID(current_user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )

    # Verify ownership or admin
    team, requester_role = await verify_team_ownership_or_admin(
        team_id, current_user, db
    )

    # Prevent owner from removing themselves
    if target_user_uuid == requester_uuid and requester_role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team owner cannot remove themselves. Transfer ownership first."
        )

    # Delete member
    result = await db.execute(
        delete(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == target_user_uuid
        )
    )
    await db.commit()


@router.put("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_member_role(
    team_id: str,
    user_id: str,
    request: UpdateMemberRoleRequest,
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamMemberResponse:
    """
    Update a member's role. Owner only.

    Owner cannot change their own role.
    """
    try:
        target_user_uuid = uuid.UUID(user_id)
        requester_uuid = uuid.UUID(current_user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )

    # Verify ownership
    team = await verify_team_ownership(team_id, current_user, db)

    # Prevent owner from changing their own role
    if target_user_uuid == requester_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot change their own role"
        )

    # Get member
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == target_user_uuid
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )

    member.role = request.role
    await db.commit()

    # Get user data for response
    user_data = await db.execute(select(User).where(User.id == target_user_uuid))
    user = user_data.scalar_one()

    return TeamMemberResponse(
        user_id=user_id,
        email=user.email,
        name=user.name,
        role=request.role,
        joined_at=member.joined_at.isoformat()
    )


@router.post("/{team_id}/transfer-ownership/{user_id}", status_code=status.HTTP_200_OK)
async def transfer_ownership(
    team_id: str,
    user_id: str,
    current_user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamResponse:
    """
    Transfer team ownership to another member. Current owner becomes admin.

    Only the current owner can transfer ownership.
    The new owner must already be a team member.
    """
    try:
        target_user_uuid = uuid.UUID(user_id)
        requester_uuid = uuid.UUID(current_user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )

    # Verify current ownership
    team = await verify_team_ownership(team_id, current_user, db)

    # Get target member
    target_member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == target_user_uuid
        )
    )
    target_member = target_member_result.scalar_one_or_none()
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user is not a team member"
        )

    # Get current owner's member record
    owner_member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == requester_uuid
        )
    )
    owner_member = owner_member_result.scalar_one_or_none()

    # Transfer ownership
    team.owner_id = target_user_uuid
    target_member.role = "owner"

    # Demote previous owner to admin
    if owner_member:
        owner_member.role = "admin"

    await db.commit()
    await db.refresh(team)

    # Get member count
    count_result = await db.execute(select(TeamMember).where(TeamMember.team_id == team.id))

    return TeamResponse(
        id=str(team.id),
        name=team.name,
        slug=team.slug,
        owner_id=str(team.owner_id),
        created_at=team.created_at.isoformat(),
        members_count=len(count_result.scalars().all())
    )
