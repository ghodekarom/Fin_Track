from datetime import date
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.models.category import Category
from app.models.expense import Expense
from app.models.budget import Budget


@pytest.mark.asyncio
async def test_quick_add_unauthenticated(client: AsyncClient):
    """Unauthenticated quick add requests return 401."""
    res1 = await client.post("/api/ai/quick-add/parse", json={"text": "Spent 200 on pizza"})
    assert res1.status_code == 401

    res2 = await client.get("/api/ai/health-score")
    assert res2.status_code == 401


@pytest.mark.asyncio
async def test_quick_add_and_health_score(client: AsyncClient, test_user, db_session):
    """Test natural language expense parsing, saving, and financial health scoring."""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Setup categories
    cat_dining = Category(name="Food & Dining", user_id=test_user.id)
    cat_transit = Category(name="Transportation", user_id=test_user.id)
    db_session.add_all([cat_dining, cat_transit])
    await db_session.commit()
    await db_session.refresh(cat_dining)
    await db_session.refresh(cat_transit)

    # Setup overall budget
    b_overall = Budget(
        user_id=test_user.id,
        scope="overall",
        limit_amount=Decimal("25000.00"),
        period_month=month_start,
    )
    db_session.add(b_overall)
    await db_session.commit()

    # Login
    login_res = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Parse natural language expense
    parse_res = await client.post(
        "/api/ai/quick-add/parse",
        headers=headers,
        json={"text": "Spent 450 on Uber ride yesterday via upi"},
    )
    assert parse_res.status_code == 200
    draft = parse_res.json()
    assert draft["amount"] == 450.0
    assert draft["payment_mode"] == "upi"
    assert "Transportation" in draft["category_name"] or draft["category_id"] is not None

    # 2. Confirm and save parsed expense
    confirm_res = await client.post(
        "/api/ai/quick-add/confirm",
        headers=headers,
        json={
            "title": draft["title"],
            "amount": draft["amount"],
            "category_id": draft["category_id"] or str(cat_transit.id),
            "expense_date": draft["expense_date"],
            "payment_mode": draft["payment_mode"],
            "notes": draft.get("notes"),
        },
    )
    assert confirm_res.status_code == 200
    created = confirm_res.json()
    assert float(created["amount"]) == 450.0

    # 3. Calculate Financial Health Score
    health_res = await client.get("/api/ai/health-score", headers=headers)
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert 0 <= health_data["health_score"] <= 100
    assert health_data["letter_grade"] in ["A+", "A", "B", "C", "D"]
    assert "pillars" in health_data
    assert "executive_summary" in health_data
    assert len(health_data["key_achievements"]) > 0
