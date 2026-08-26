import pytest
from httpx import AsyncClient
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense


@pytest.mark.asyncio
async def test_create_and_conflict_budgets(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    cat = Category(name="Rent")
    db_session.add(cat)
    await db_session.commit()

    # 1. Create Overall Budget
    payload_overall = {
        "scope": "overall",
        "period_month": "2026-08-01",
        "limit_amount": 50000.00,
    }
    response = await client.post("/api/budgets", json=payload_overall)
    assert response.status_code == 201
    assert response.json()["scope"] == "overall"

    # 2. Check conflict on duplicate overall budget
    conflict_overall = await client.post("/api/budgets", json=payload_overall)
    assert conflict_overall.status_code == 409

    # 3. Create Category Budget
    payload_cat = {
        "scope": "category",
        "category_id": str(cat.id),
        "period_month": "2026-08-01",
        "limit_amount": 15000.00,
    }
    response_cat = await client.post("/api/budgets", json=payload_cat)
    assert response_cat.status_code == 201
    assert response_cat.json()["scope"] == "category"

    # 4. Check conflict on duplicate category budget
    conflict_cat = await client.post("/api/budgets", json=payload_cat)
    assert conflict_cat.status_code == 409


@pytest.mark.asyncio
async def test_budget_status_calculation(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    cat = Category(name="Food")
    db_session.add(cat)
    await db_session.commit()

    # Create overall budget (limit 1000)
    payload_overall = {
        "scope": "overall",
        "period_month": "2026-08-01",
        "limit_amount": 1000.00,
    }
    await client.post("/api/budgets", json=payload_overall)

    # Create category budget (limit 500)
    payload_cat = {
        "scope": "category",
        "category_id": str(cat.id),
        "period_month": "2026-08-01",
        "limit_amount": 500.00,
    }
    await client.post("/api/budgets", json=payload_cat)

    # Add expense under category (amount 460 -> near limit >= 90%)
    expense1 = Expense(
        title="Restaurant Bill",
        category_id=cat.id,
        amount=460.00,
        expense_date=date(2026, 8, 15),
    )
    db_session.add(expense1)
    await db_session.commit()

    # Get budget statuses
    response = await client.get("/api/budgets/status?period_month=2026-08-01")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Map responses by scope
    status_map = {b["scope"]: b for b in data}

    # Food status (spent 460/500 = 92% -> near_limit)
    assert float(status_map["category"]["spent"]) == 460.00
    assert float(status_map["category"]["remaining"]) == 40.00
    assert status_map["category"]["status"] == "near_limit"

    # Overall status (spent 460/1000 = 46% -> on_track)
    assert float(status_map["overall"]["spent"]) == 460.00
    assert float(status_map["overall"]["remaining"]) == 540.00
    assert status_map["overall"]["status"] == "on_track"

    # Add another expense that blows the budget
    expense2 = Expense(
        title="More Food",
        category_id=cat.id,
        amount=100.00,
        expense_date=date(2026, 8, 16),
    )
    db_session.add(expense2)
    await db_session.commit()

    # Check status again
    response = await client.get("/api/budgets/status?period_month=2026-08-01")
    data = response.json()
    status_map = {b["scope"]: b for b in data}

    # Food status (spent 560/500 -> over_budget)
    assert status_map["category"]["status"] == "over_budget"
