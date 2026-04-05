from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field


class RecordCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Must be a positive number", examples=[5000.00])
    type: Literal["income", "expense"] = Field(..., examples=["income"])
    category: str = Field(..., min_length=1, max_length=50, examples=["salary"])
    date: dt.date = Field(..., examples=["2026-04-01"])
    description: str | None = Field(None, max_length=500, examples=["Monthly salary payment"])


class RecordUpdate(BaseModel):
    amount: float | None = Field(None, gt=0)
    type: Literal["income", "expense"] | None = None
    category: str | None = Field(None, min_length=1, max_length=50)
    date: dt.date | None = None
    description: str | None = Field(None, max_length=500)


class RecordResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    type: str
    category: str
    date: dt.date
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = {"from_attributes": True}


class RecordListResponse(BaseModel):
    data: list[RecordResponse]
    total: int
    page: int
    pages: int
