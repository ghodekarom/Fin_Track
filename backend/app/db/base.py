# Import all the models, so that Base has them before being
# imported by Alembic or script runner
from app.db.base_class import Base  # noqa
from app.models.budget import Budget  # noqa
from app.models.category import Category  # noqa
from app.models.expense import Expense  # noqa
