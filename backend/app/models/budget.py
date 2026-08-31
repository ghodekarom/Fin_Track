import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
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
    user: Mapped["User"] = relationship("User", back_populates="budgets")
    category: Mapped["Category"] = relationship("Category", back_populates="budgets")

    __table_args__ = (
        CheckConstraint("limit_amount > 0", name="check_budgets_limit_positive"),
        CheckConstraint(
            "scope IN ('overall', 'category')", name="check_budgets_scope"
        ),
        CheckConstraint(
            "(scope = 'overall' AND category_id IS NULL) OR (scope = 'category' AND category_id IS NOT NULL)",
            name="check_budgets_category_id_scope_nullability",
        ),
        Index("idx_budgets_user_id", user_id),
        Index(
            "idx_budgets_unique_user_overall",
            user_id,
            scope,
            period_month,
            unique=True,
            postgresql_where=(category_id.is_(None)),
        ),
        Index(
            "idx_budgets_unique_user_category",
            user_id,
            scope,
            category_id,
            period_month,
            unique=True,
            postgresql_where=(category_id.isnot(None)),
        ),
    )
