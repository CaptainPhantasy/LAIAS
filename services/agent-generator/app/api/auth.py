"""
Authentication and Authorization Middleware for LAIAS.

Dev-mode auth using X-User-Id header for now.
TODO: Add production auth (JWT/OAuth) later.
"""

from typing import Optional, List
from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.database import get_db
from app.models.team import Team, TeamMember, User


# =============================================================================
# Models
# =============================================================================

class DevUser(BaseModel):
    """Dev-mode user from header."""
    id: str
    email: str = "dev@laias.local"
    name: str = "Dev User"


# =============================================================================
# Dependencies
# =============================================================================

async def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    x_user_name: Optional[str] = Header(None, alias="X-User-Name"),
) -> DevUser:
    """
    Get current user from headers (dev mode).

    In production, this would validate JWT tokens.
    For dev, we accept X-User-Id header.

    If no header provided, create a dev user for testing.
    """
    if not x_user_id:
        # Create a dev user for testing
        return DevUser(
            id="00000000-0000-0000-0000-000000000000",
            email="dev@laias.local",
            name="Dev User"
        )

    # Validate UUID format
    try:
        uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )

    return DevUser(
        id=x_user_id,
        email=x_user_email or "dev@laias.local",
        name=x_user_name or "Dev User"
    )


# =============================================================================
# Authorization Helpers
# =============================================================================

class TeamRoleChecker:
    """
    Check if user has required role in team.

    Role hierarchy: owner > admin > member > viewer
    """

    ROLE_HIERARCHY = {
        "owner": 4,
        "admin": 3,
        "member": 2,
        "viewer": 1
    }

    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
        # Minimum required level
        self.min_level = min(self.ROLE_HIERARCHY.get(r, 0) for r in required_roles)

    async def __call__(
        self,
        team_id: str,
        user: DevUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> DevUser:
        """
        Check if user has required role in team.

        Raises HTTPException if unauthorized.
        """
        try:
            team_uuid = uuid.UUID(team_id)
            user_uuid = uuid.UUID(user.id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format"
            )

        # Get user's role in this team
        result = await db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_uuid,
                TeamMember.user_id == user_uuid
            )
        )
        membership = result.scalar_one_or_none()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this team"
            )

        user_level = self.ROLE_HIERARCHY.get(membership.role, 0)
        if user_level < self.min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {self.required_roles[0]} role or higher"
            )

        return user


async def get_team_role(
    team_id: str,
    user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    Get user's role in a team.

    Returns the role string or raises if not a member.
    """
    try:
        team_uuid = uuid.UUID(team_id)
        user_uuid = uuid.UUID(user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )

    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_uuid,
            TeamMember.user_id == user_uuid
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )

    return membership.role


async def verify_team_ownership_or_admin(
    team_id: str,
    user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> tuple[Team, str]:
    """
    Verify user is owner or admin of team.

    Returns (team, user_role) tuple.
    Raises HTTPException if not authorized.
    """
    try:
        team_uuid = uuid.UUID(team_id)
        user_uuid = uuid.UUID(user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )

    # Get team
    team_result = await db.execute(select(Team).where(Team.id == team_uuid))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check if user is owner (via owner_id field)
    if team.owner_id == user_uuid:
        return team, "owner"

    # Check team membership for admin role
    member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_uuid,
            TeamMember.user_id == user_uuid
        )
    )
    membership = member_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )

    if membership.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can perform this action"
        )

    return team, membership.role


async def verify_team_ownership(
    team_id: str,
    user: DevUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Team:
    """
    Verify user is owner of team.

    Returns the Team object.
    Raises HTTPException if not owner.
    """
    try:
        team_uuid = uuid.UUID(team_id)
        user_uuid = uuid.UUID(user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )

    # Get team
    team_result = await db.execute(select(Team).where(Team.id == team_uuid))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check ownership
    if team.owner_id != user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can perform this action"
        )

    return team


def require_team_role(role: str) -> TeamRoleChecker:
    """Factory for role checker - accepts single role or comma-separated list."""
    roles = [r.strip() for r in role.split(",")]
    return TeamRoleChecker(roles)


require_admin_or_owner = require_team_role("admin,owner")
require_owner = require_team_role("owner")
