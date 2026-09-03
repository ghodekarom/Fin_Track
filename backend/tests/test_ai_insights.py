from datetime import date, timedelta
import pytest
from httpx import AsyncClient

from app.models.category import Category
from app.models.expense import Expense
from app.models.budget import Budget


@pytest.mark.asyncio
async def test_ai_insights_unauthenticated(client: AsyncClient):
    """Accessing AI insights without authentication must return 401."""
    response = await client.get("/api/ai/insights")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ai_insights_empty_history(client: AsyncClient, test_user):
    """User with no expenses receives onboarding starter recommendations."""
    # Login to get access token
    login_res = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/ai/insights", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "insights" in data
    assert "total_potential_monthly_savings" in data
    assert len(data["insights"]) >= 1


@pytest.mark.asyncio
async def test_ai_insights_with_expenses_and_budget(
    client: AsyncClient, test_user, db_session
):
    """User with expenses and exceeded budget receives tailored alerts."""
    # Create a custom category
    cat = Category(name="Leisure Dining", user_id=test_user.id)
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    # Add expenses
    today = date.today()
    exp1 = Expense(
        user_id=test_user.id,
        category_id=cat.id,
        amount=3500.0,
        expense_date=today,
        title="Fancy Dinner",
        payment_mode="card",
    )
    exp2 = Expense(
        user_id=test_user.id,
        category_id=cat.id,
        amount=2500.0,
        expense_date=today - timedelta(days=2),
        title="Lunch with Friends",
        payment_mode="card",
    )
    db_session.add_all([exp1, exp2])

    # Set budget for this category lower than spent (to trigger budget alert)
    budget = Budget(
        user_id=test_user.id,
        scope="category",
        category_id=cat.id,
        limit_amount=4000.0,
        period_month=date(today.year, today.month, 1),
    )
    db_session.add(budget)
    await db_session.commit()

    # Login
    login_res = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Force refresh insights
    res = await client.post("/api/ai/insights/refresh", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "insights" in data
    types = [i["type"] for i in data["insights"]]
    assert "budget_alert" in types or "high_impact" in types or "quick_win" in types
    assert data["total_potential_monthly_savings"] >= 0
