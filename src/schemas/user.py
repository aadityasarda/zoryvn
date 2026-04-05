from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    
    id: str
    name: str
    email: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    role: Literal["viewer", "analyst", "admin"] | None = None
    status: Literal["active", "inactive"] | None = None


class UserListResponse(BaseModel):
    data: list[UserResponse]
    total: int
    page: int
    pages: int
