from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import require_role
from src.models.user import User
from src.schemas.record import (
    RecordCreate,
    RecordUpdate,
    RecordResponse,
    RecordListResponse,
)
from src.services import record_service

router = APIRouter(prefix="/api/records", tags=["Financial Records"])


@router.post(
    "",
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a financial record (Admin only)",
)
async def create_record(
    record: RecordCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    
    new_record = await record_service.create_record(
        db=db,
        user_id=current_user.id,
        amount=record.amount,
        type=record.type,
        category=record.category,
        date=record.date,
        description=record.description,
    )
    return new_record


@router.get(
    "",
    response_model=RecordListResponse,
    summary="List financial records",
    description="Get paginated, filtered list of records. Supports filtering by type, category, date range, and text search.",
)
async def list_records(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    type: str | None = Query(None, description="Filter by type: income or expense"),
    category: str | None = Query(None, description="Filter by category"),
    start_date: date | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
    search: str | None = Query(None, description="Search in description"),
    current_user: User = Depends(require_role("viewer", "analyst", "admin")),
    db: AsyncSession = Depends(get_db),
):
    result = await record_service.get_records(
        db=db,
        current_user=current_user,
        page=page,
        limit=limit,
        type_filter=type,
        category_filter=category,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    return result


@router.get(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Get a single record",
)
async def get_record(
    record_id: str,
    current_user: User = Depends(require_role("viewer", "analyst", "admin")),
    db: AsyncSession = Depends(get_db),
):
    record = await record_service.get_record_by_id(db, record_id, current_user)
    return record


@router.put(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Update a financial record (Admin only)",
)
async def update_record(
    record_id: str,
    update_data: RecordUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    record = await record_service.update_record(
        db, record_id, update_data.model_dump(exclude_none=True), current_user
    )
    return record


@router.delete(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Soft-delete a record (Admin only)",
    description="Marks the record as deleted. Does not physically remove it (audit trail).",
)
async def delete_record(
    record_id: str,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    record = await record_service.delete_record(db, record_id, current_user)
    return record
