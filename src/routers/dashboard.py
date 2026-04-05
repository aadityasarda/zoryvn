from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import require_role
from src.models.user import User
from src.schemas.dashboard import (
    SummaryResponse,
    CategoryTotalsResponse,
    TrendsResponse,
    RecentTransactionsResponse,
)
from src.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Analytics"])


@router.get(
    "/summary",
    response_model=SummaryResponse,
    summary="Get financial summary",
    description="Returns total income, total expenses, net balance, and record count.",
)
async def get_summary(
    current_user: User = Depends(require_role("analyst", "admin")),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_service.get_summary(db, current_user)


@router.get(
    "/category-totals",
    response_model=CategoryTotalsResponse,
    summary="Get category-wise totals",
    description="Returns income/expense totals grouped by category, ordered by total descending.",
)
async def get_category_totals(
    current_user: User = Depends(require_role("analyst", "admin")),
    db: AsyncSession = Depends(get_db),
):
    data = await dashboard_service.get_category_totals(db, current_user)
    return {"data": data}


@router.get(
    "/trends",
    response_model=TrendsResponse,
    summary="Get income/expense trends",
    description="Returns weekly or monthly income/expense trends (last 12 periods).",
)
async def get_trends(
    interval: str = Query(
        "monthly",
        description="Trend interval: 'weekly' or 'monthly'",
        regex="^(weekly|monthly)$",
    ),
    current_user: User = Depends(require_role("analyst", "admin")),
    db: AsyncSession = Depends(get_db),
):
    data = await dashboard_service.get_trends(db, current_user, interval)
    return {"interval": interval, "data": data}


@router.get(
    "/recent",
    response_model=RecentTransactionsResponse,
    summary="Get recent transactions",
    description="Returns the last N transactions (default: 10).",
)
async def get_recent_transactions(
    limit: int = Query(10, ge=1, le=50, description="Number of transactions"),
    current_user: User = Depends(require_role("analyst", "admin")),
    db: AsyncSession = Depends(get_db),
):
    records = await dashboard_service.get_recent_transactions(db, current_user, limit)
    return {"data": records}
