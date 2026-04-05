from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.user import User
from src.utils.errors import AppError
from src.utils.security import hash_password, verify_password, create_access_token


async def register_user(
    db: AsyncSession, name: str, email: str, password: str
) -> User:
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise AppError("A user with this email already exists", status_code=409)

    # Create user with hashed password
    user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role="viewer",
        status="active",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user) 

    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> str:
    
    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise AppError("Invalid email or password", status_code=401)

    # Verify password
    if not verify_password(password, user.password):
        raise AppError("Invalid email or password", status_code=401)

    # Check active status
    if user.status != "active":
        raise AppError("Account has been deactivated", status_code=401)

    # Generate JWT token
    token = create_access_token(user_id=user.id, role=user.role)
    return token
