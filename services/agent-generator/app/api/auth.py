"""
Authentication and Authorization Middleware for LAIAS.

Supports both JWT-based authentication and dev-mode header-based auth.
Dev mode is controlled by AUTH_DEV_MODE environment variable.
"""

import os
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.team import Team, TeamMember, User

# =============================================================================
# Configuration
# =============================================================================

# JWT Settings - in production, these should be environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Dev mode toggle - set AUTH_DEV_MODE=false in production
AUTH_DEV_MODE = os.getenv("AUTH_DEV_MODE", "true").lower() == "true"

# Password hashing — using bcrypt directly (passlib incompatible with bcrypt>=4.1)

# Bearer token scheme
security = HTTPBearer(auto_error=False)


# =============================================================================
# Models
# =============================================================================


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # user_id
    email: str | None = None
    exp: datetime | None = None
    iat: datetime | None = None
    type: str = "access"  # access or refresh


class CurrentUser(BaseModel):
    """Authenticated user."""

    id: str
    email: str
    name: str


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request body."""

    email: EmailStr
    password: str
    name: str


# =============================================================================
# Password Utilities
# =============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8")[:72],
        hashed_password.encode("utf-8"),
    )


def hash_password(password: str) -> str:
    """Hash a password with bcrypt. Truncates to 72 bytes per bcrypt spec."""
    return bcrypt.hashpw(
        password.encode("utf-8")[:72],
        bcrypt.gensalt(),
    ).decode("utf-8")


# =============================================================================
# JWT Token Utilities
# =============================================================================


def create_access_token(user_id: str, email: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expire, "iat": datetime.now(UTC), "type": "refresh"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# Authentication Dependencies
# =============================================================================


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_name: str | None = Header(None, alias="X-User-Name"),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    Get current user from JWT token or dev-mode headers.

    Priority:
    1. JWT Bearer token (production)
    2. X-User-Id header (dev mode)
    3. Fallback dev user (dev mode only)
    """
    # Try JWT authentication first
    if credentials:
        token_payload = decode_token(credentials.credentials)

        if token_payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Use access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Look up user in database
        try:
            user_uuid = uuid.UUID(token_payload.sub)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID in token"
            )

        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return CurrentUser(id=str(user.id), email=user.email, name=user.name)

    # Dev mode: try header-based auth
    if AUTH_DEV_MODE:
        if x_user_id:
            # Validate UUID format
            try:
                uuid.UUID(x_user_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID format"
                )

            return CurrentUser(
                id=x_user_id,
                email=x_user_email or "dev@laias.local",
                name=x_user_name or "Dev User",
            )

        # Fallback to dev user
        return CurrentUser(
            id="00000000-0000-0000-0000-000000000000", email="dev@laias.local", name="Dev User"
        )

    # No auth available and dev mode disabled
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


# =============================================================================
# Authorization Helpers
# =============================================================================


class TeamRoleChecker:
    """
    Check if user has required role in team.

    Role hierarchy: owner > admin > member > viewer
    """

    ROLE_HIERARCHY = {"owner": 4, "admin": 3, "member": 2, "viewer": 1}

    def __init__(self, required_roles: list[str]):
        self.required_roles = required_roles
        # Minimum required level
        self.min_level = min(self.ROLE_HIERARCHY.get(r, 0) for r in required_roles)

    async def __call__(
        self,
        team_id: str,
        user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> CurrentUser:
        """
        Check if user has required role in team.

        Raises HTTPException if unauthorized.
        """
        try:
            team_uuid = uuid.UUID(team_id)
            user_uuid = uuid.UUID(user.id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")

        # Get user's role in this team
        result = await db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_uuid, TeamMember.user_id == user_uuid
            )
        )
        membership = result.scalar_one_or_none()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this team"
            )

        user_level = self.ROLE_HIERARCHY.get(membership.role, 0)
        if user_level < self.min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {self.required_roles[0]} role or higher",
            )

        return user


async def get_team_role(
    team_id: str, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> str:
    """
    Get user's role in a team.

    Returns the role string or raises if not a member.
    """
    try:
        team_uuid = uuid.UUID(team_id)
        user_uuid = uuid.UUID(user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")

    result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_uuid, TeamMember.user_id == user_uuid)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this team"
        )

    return membership.role


async def verify_team_ownership_or_admin(
    team_id: str, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")

    # Get team
    team_result = await db.execute(select(Team).where(Team.id == team_uuid))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check if user is owner (via owner_id field)
    if team.owner_id == user_uuid:
        return team, "owner"

    # Check team membership for admin role
    member_result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_uuid, TeamMember.user_id == user_uuid)
    )
    membership = member_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this team"
        )

    if membership.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can perform this action",
        )

    return team, membership.role


async def verify_team_ownership(
    team_id: str, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")

    # Get team
    team_result = await db.execute(select(Team).where(Team.id == team_uuid))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check ownership
    if team.owner_id != user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can perform this action",
        )

    return team


def require_team_role(role: str) -> TeamRoleChecker:
    """Factory for role checker - accepts single role or comma-separated list."""
    roles = [r.strip() for r in role.split(",")]
    return TeamRoleChecker(roles)


# Convenience aliases
require_admin_or_owner = require_team_role("admin,owner")
require_owner = require_team_role("owner")


# =============================================================================
# Backward Compatibility
# =============================================================================

# Alias for backward compatibility with existing code
DevUser = CurrentUser
