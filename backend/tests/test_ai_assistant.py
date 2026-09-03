from datetime import date
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.models.category import Category
from app.models.expense import Expense
from app.models.budget import Budget


@pytest.mark.asyncio
async def test_ai_assistant_unauthenticated(client: AsyncClient):
    """Querying AI assistant without authentication returns 401."""
    res = await client.post("/api/ai/ask", json={"question": "What is my budget?"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_ai_assistant_authenticated_queries(client: AsyncClient, test_user, db_session):
    """Authenticated user asks questions about budget, categories, and affordability."""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Setup categories, budgets, and expenses
    cat_food = Category(name="Food", user_id=test_user.id)
    cat_tech = Category(name="Electronics", user_id=test_user.id)
    db_session.add_all([cat_food, cat_tech])
    await db_session.commit()
    await db_session.refresh(cat_food)
    await db_session.refresh(cat_tech)

    exp1 = Expense(
        user_id=test_user.id,
        category_id=cat_food.id,
        amount=1200.0,
        expense_date=today,
        title="Dinner Buffet",
        payment_mode="card",
    )
    b_overall = Budget(
        user_id=test_user.id,
        scope="overall",
        limit_amount=Decimal("15000.00"),
        period_month=month_start,
    )
    db_session.add_all([exp1, b_overall])
    await db_session.commit()

    # Login
    login_res = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Ask about budget
    res1 = await client.post(
        "/api/ai/ask",
        headers=headers,
        json={"question": "How much budget do I have left?"},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert "answer" in data1
    assert "15,000" in data1["answer"] or "1200" in data1["answer"]
    assert len(data1["suggested_followups"]) > 0

    # 2. Ask about affordability
    res2 = await client.post(
        "/api/ai/ask",
        headers=headers,
        json={"question": "Can I afford a ₹3,500 gadget?"},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert "answer" in data2
    assert "afford" in data2["answer"].lower()

    # 3. Ask about category
    res3 = await client.post(
        "/api/ai/ask",
        headers=headers,
        json={"question": "How much did I spend on Food?"},
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert "1,200" in data3["answer"] or "Food" in data3["answer"]
