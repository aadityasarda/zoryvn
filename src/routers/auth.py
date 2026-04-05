from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from src.schemas.user import UserResponse
from src.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. Default role is 'viewer' (least privilege).",
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.register_user(
        db=db,
        name=request.name,
        email=request.email,
        password=request.password,
    )
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get JWT token",
    description="Authenticate with email and password. Returns a JWT bearer token.",
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    
    token = await auth_service.authenticate_user(
        db=db,
        email=request.email,
        password=request.password,
    )
    return TokenResponse(access_token=token)
