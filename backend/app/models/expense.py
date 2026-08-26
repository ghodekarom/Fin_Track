import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="expenses")

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_expenses_amount_positive"),
        CheckConstraint(
            "expense_date <= CURRENT_DATE", name="check_expenses_date_not_future"
        ),
        CheckConstraint(
            "payment_mode IN ('cash', 'card', 'upi', 'other')",
            name="check_expenses_payment_mode",
        ),
        Index("idx_expenses_category_id", category_id),
        Index("idx_expenses_expense_date", expense_date),
        Index("idx_expenses_amount", amount),
        # Since trigram indexes depend on PostgreSQL extensions, we will define a standard btree index
        # on title and notes which is fully compatible out-of-the-box.
        Index("idx_expenses_title_notes", title, notes),
    )
