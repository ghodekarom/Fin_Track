import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scope: Mapped[str] = mapped_column(String(10), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
    )
    period_month: Mapped[date] = mapped_column(Date, nullable=False)
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
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
    category: Mapped["Category"] = relationship("Category", back_populates="budgets")

    __table_args__ = (
        CheckConstraint("limit_amount > 0", name="check_budgets_limit_positive"),
        CheckConstraint(
            "scope IN ('overall', 'category')", name="check_budgets_scope"
        ),
        # Ensure category_id is NULL for overall budget, and NOT NULL for category budget
        CheckConstraint(
            "(scope = 'overall' AND category_id IS NULL) OR (scope = 'category' AND category_id IS NOT NULL)",
            name="check_budgets_category_id_scope_nullability",
        ),
        # Enforce unique constraint for overall budget per month
        Index(
            "idx_budgets_unique_overall",
            scope,
            period_month,
            unique=True,
            postgresql_where=(category_id.is_(None)),
        ),
        # Enforce unique constraint for category budget per category per month
        Index(
            "idx_budgets_unique_category",
            scope,
            category_id,
            period_month,
            unique=True,
            postgresql_where=(category_id.isnot(None)),
        ),
    )
