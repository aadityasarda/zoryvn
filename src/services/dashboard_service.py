from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_, extract, cast, String

from src.models.record import FinancialRecord
from src.models.user import User

def _base_conditions(current_user: User) -> list:
    conditions = [FinancialRecord.is_deleted == False]  
    if current_user.role != "admin":
        conditions.append(FinancialRecord.user_id == current_user.id)
    return conditions


async def get_summary(db: AsyncSession, current_user: User) -> dict:
    where = and_(*_base_conditions(current_user))

    result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == "income", FinancialRecord.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == "expense", FinancialRecord.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("total_expenses"),
            func.count(FinancialRecord.id).label("record_count"),
        ).where(where)
    )

    row = result.one()
    total_income = float(row.total_income)
    total_expenses = float(row.total_expenses)

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": round(total_income - total_expenses, 2),
        "record_count": row.record_count,
    }


async def get_category_totals(db: AsyncSession, current_user: User) -> list[dict]:
    where = and_(*_base_conditions(current_user))

    result = await db.execute(
        select(
            FinancialRecord.category,
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .where(where)
        .group_by(FinancialRecord.category, FinancialRecord.type)
        .order_by(func.sum(FinancialRecord.amount).desc())
    )

    return [
        {
            "category": row.category,
            "type": row.type,
            "total": float(row.total),
            "count": row.count,
        }
        for row in result.all()
    ]


async def get_trends(
    db: AsyncSession, current_user: User, interval: str = "monthly"
) -> list[dict]:
    where = and_(*_base_conditions(current_user))

    if interval == "weekly":
        period_expr = func.to_char(FinancialRecord.date, 'IYYY-"W"IW')
    else:
        period_expr = func.to_char(FinancialRecord.date, 'YYYY-MM')

    result = await db.execute(
        select(
            period_expr.label("period"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == "income", FinancialRecord.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("income"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == "expense", FinancialRecord.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("expenses"),
        )
        .where(where)
        .group_by(period_expr)
        .order_by(period_expr.desc())
        .limit(12)
    )

    return [
        {
            "period": row.period,
            "income": float(row.income),
            "expenses": float(row.expenses),
            "net": round(float(row.income) - float(row.expenses), 2),
        }
        for row in result.all()
    ]


async def get_recent_transactions(
    db: AsyncSession, current_user: User, limit: int = 10
) -> list:
    where = and_(*_base_conditions(current_user))

    result = await db.execute(
        select(FinancialRecord)
        .where(where)
        .order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc())
        .limit(limit)
    )

    return result.scalars().all()

