
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.models.user import User
from src.utils.errors import AppError


async def get_users(
    db: AsyncSession, page: int = 1, limit: int = 20
) -> dict:
    offset = (page - 1) * limit

    # Get total count
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar()

    # Get paginated users
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    )
    users = result.scalars().all()

    return {
        "data": users,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if total > 0 else 1,
    }


async def get_user_by_id(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AppError("User not found", status_code=404)

    return user


async def update_user(
    db: AsyncSession, user_id: str, update_data: dict
) -> User:
    user = await get_user_by_id(db, user_id)

    # Apply updates
    for field, value in update_data.items():
        if value is not None:
            setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user_id: str) -> User:
    user = await get_user_by_id(db, user_id)

    if user.status == "inactive":
        raise AppError("User is already inactive", status_code=400)

    user.status = "inactive"
    await db.flush()
    await db.refresh(user)
    return user
