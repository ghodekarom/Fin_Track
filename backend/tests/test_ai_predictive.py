from datetime import date, timedelta
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.models.category import Category
from app.models.expense import Expense
from app.models.budget import Budget


@pytest.mark.asyncio
async def test_predictive_budget_unauthenticated(client: AsyncClient):
    """Accessing predictive budget without authentication returns 401."""
    res = await client.get("/api/ai/predictive-budget")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_predictive_budget_authenticated(client: AsyncClient, test_user, db_session):
    """Authenticated user receives burn rate, projected overage, and safe daily spend."""
    # Create category, expense, and budget
    today = date.today()
    month_start = date(today.year, today.month, 1)

    cat = Category(name="Transit", user_id=test_user.id)
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    exp = Expense(
        user_id=test_user.id,
        category_id=cat.id,
        amount=1500.0,
        expense_date=today,
        title="Metro Passes",
        payment_mode="card",
    )
    b_overall = Budget(
        user_id=test_user.id,
        scope="overall",
        limit_amount=Decimal("20000.00"),
        period_month=month_start,
    )
    b_cat = Budget(
        user_id=test_user.id,
        scope="category",
        category_id=cat.id,
        limit_amount=Decimal("3000.00"),
        period_month=month_start,
    )
    db_session.add_all([exp, b_overall, b_cat])
    await db_session.commit()

    # Login
    login_res = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch predictive budget
    res = await client.get("/api/ai/predictive-budget", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "velocity" in data
    velocity = data["velocity"]
    assert velocity["current_spent"] >= 1500.0
    assert velocity["days_elapsed"] >= 1
    assert velocity["days_remaining"] >= 1
    assert velocity["safe_daily_spend"] >= 0
    assert "risk_level" in velocity

    # Apply suggested budget
    apply_res = await client.post(
        "/api/ai/predictive-budget/apply",
        headers=headers,
        json={"category_id": str(cat.id), "amount": 3500.0},
    )
    assert apply_res.status_code == 200
    assert apply_res.json()["success"] is True
