from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import require_role
from src.models.user import User
from src.schemas.user import UserResponse, UserUpdate, UserListResponse
from src.services import user_service

router = APIRouter(prefix="/api/users", tags=["User Management"])


@router.get(
    "",
    response_model=UserListResponse,
    summary="List all users (Admin only)",
    description="Get a paginated list of all users in the system.",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    result = await user_service.get_users(db, page=page, limit=limit)
    return result


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user details (Admin only)",
)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_by_id(db, user_id)
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user (Admin only)",
    description="Update a user's name, role, or status. Only provided fields are updated.",
)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.update_user(
        db, user_id, update_data.model_dump(exclude_none=True)
    )
    return user


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    summary="Deactivate user (Admin only)",
    description="Sets user status to 'inactive'. Does not delete the user.",
)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.deactivate_user(db, user_id)
    return user
