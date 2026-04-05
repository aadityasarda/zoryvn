from __future__ import annotations

import datetime as dt
from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    record_count: int


class CategoryTotal(BaseModel):
    category: str
    type: str
    total: float
    count: int


class CategoryTotalsResponse(BaseModel):
    data: list[CategoryTotal]


class TrendPoint(BaseModel):
    period: str  
    income: float
    expenses: float
    net: float


class TrendsResponse(BaseModel):
    interval: str  
    data: list[TrendPoint]


class RecentTransaction(BaseModel):
    id: str
    amount: float
    type: str
    category: str
    date: dt.date
    description: str | None

    model_config = {"from_attributes": True}


class RecentTransactionsResponse(BaseModel):
    data: list[RecentTransaction]
