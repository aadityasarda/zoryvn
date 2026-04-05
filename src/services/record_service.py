import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.models.record import FinancialRecord
from src.models.user import User
from src.utils.errors import AppError


async def create_record(
    db: AsyncSession,
    user_id: str,
    amount: float,
    type: str,
    category: str,
    date,
    description: str | None = None,
) -> FinancialRecord:
    record = FinancialRecord(
        user_id=user_id,
        amount=amount,
        type=type,
        category=category,
        date=date,
        description=description,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_records(
    db: AsyncSession,
    current_user: User,
    page: int = 1,
    limit: int = 20,
    type_filter: str | None = None,
    category_filter: str | None = None,
    start_date=None,
    end_date=None,
    search: str | None = None,
) -> dict:
    
    offset = (page - 1) * limit

    # Base conditions
    conditions = [FinancialRecord.is_deleted == False]  # noqa: E712

    # Data visibility
    if current_user.role != "admin":
        conditions.append(FinancialRecord.user_id == current_user.id)

    # Apply filters
    if type_filter:
        conditions.append(FinancialRecord.type == type_filter)
    if category_filter:
        conditions.append(FinancialRecord.category == category_filter)
    if start_date:
        conditions.append(FinancialRecord.date >= start_date)
    if end_date:
        conditions.append(FinancialRecord.date <= end_date)
    if search:
        conditions.append(FinancialRecord.description.ilike(f"%{search}%"))

    where_clause = and_(*conditions)

    # Get total count
    count_result = await db.execute(
        select(func.count(FinancialRecord.id)).where(where_clause)
    )
    total = count_result.scalar()

    # Get paginated records
    result = await db.execute(
        select(FinancialRecord)
        .where(where_clause)
        .order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    records = result.scalars().all()

    return {
        "data": records,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if total > 0 else 1,
    }


async def get_record_by_id(
    db: AsyncSession, record_id: str, current_user: User
) -> FinancialRecord:
    result = await db.execute(
        select(FinancialRecord).where(
            and_(
                FinancialRecord.id == record_id,
                FinancialRecord.is_deleted == False,  # noqa: E712
            )
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        raise AppError("Record not found", status_code=404)

    # Data visibility check
    if current_user.role != "admin" and record.user_id != current_user.id:
        raise AppError("Access denied to this record", status_code=403)

    return record


async def update_record(
    db: AsyncSession, record_id: str, update_data: dict, current_user: User
) -> FinancialRecord:
    record = await get_record_by_id(db, record_id, current_user)

    for field, value in update_data.items():
        if value is not None:
            setattr(record, field, value)

    await db.flush()
    await db.refresh(record)
    return record


async def delete_record(
    db: AsyncSession, record_id: str, current_user: User
) -> FinancialRecord:
    record = await get_record_by_id(db, record_id, current_user)

    if record.is_deleted:
        raise AppError("Record is already deleted", status_code=400)

    record.is_deleted = True
    await db.flush()
    await db.refresh(record)
    return record
