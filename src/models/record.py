import uuid
from datetime import datetime, date as date_type

from sqlalchemy import String, DateTime, Date, Numeric, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True
    )  # income | expense
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    date: Mapped[date_type] = mapped_column(
        Date, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship: many records → one user
    user = relationship("User", back_populates="records")

    def __repr__(self) -> str:
        return f"<FinancialRecord {self.type} {self.amount} {self.category}>"
