"""
User API Routes.

Get and update current user information.
"""


from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.auth import DevUser, get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


# =============================================================================
# Schemas
# =============================================================================

class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    name: str | None = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User update schema."""
    name: str | None = None
    email: str | None = None


# =============================================================================
# Routes
# =============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: DevUser = Depends(get_current_user)
) -> UserResponse:
    """
    Get current user information.

    In dev mode, returns user from X-User-Id header or default dev user.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update: UserUpdate,
    current_user: DevUser = Depends(get_current_user)
) -> UserResponse:
    """
    Update current user information.

    In dev mode, updates the in-memory user.
    In production, would update database record.
    """
    # In dev mode, just return the updated data
    return UserResponse(
        id=str(current_user.id),
        email=update.email or current_user.email,
        name=update.name or current_user.name
    )
