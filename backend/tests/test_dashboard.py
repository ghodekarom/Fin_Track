import pytest
from httpx import AsyncClient
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense


@pytest.mark.asyncio
async def test_dashboard_summary_and_breakdowns(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    cat1 = Category(name="Rent")
    cat2 = Category(name="Utilities")
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    e1 = Expense(
        title="House rent",
        category_id=cat1.id,
        amount=20000.00,
        expense_date=date(2026, 8, 1),
    )
    e2 = Expense(
        title="Electricity bill",
        category_id=cat2.id,
        amount=3500.00,
        expense_date=date(2026, 8, 5),
    )
    db_session.add_all([e1, e2])
    await db_session.commit()

    # 1. Dashboard summary check
    summary_response = await client.get("/api/dashboard/summary?period_month=2026-08-01")
    assert summary_response.status_code == 200
    summary_data = summary_response.json()
    assert float(summary_data["total_spent"]) == 23500.00
    assert len(summary_data["recent_expenses"]) == 2

    # 2. Category breakdown check
    breakdown_response = await client.get(
        "/api/dashboard/charts/category-breakdown?date_from=2026-08-01&date_to=2026-08-31"
    )
    assert breakdown_response.status_code == 200
    breakdown_data = breakdown_response.json()
    assert len(breakdown_data) == 2
    assert breakdown_data[0]["category_name"] == "Rent"
    assert float(breakdown_data[0]["total_spent"]) == 20000.00

    # 3. MoM spending trend check
    trend_response = await client.get(
        "/api/dashboard/charts/spending-trend?period=daily&date_from=2026-08-01&date_to=2026-08-31"
    )
    assert trend_response.status_code == 200
    trend_data = trend_response.json()
    # Should have two data points representing the days 2026-08-01 and 2026-08-05
    assert len(trend_data) == 2


@pytest.mark.asyncio
async def test_top_categories_and_averages(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    cat1 = Category(name="Food")
    cat2 = Category(name="Transport")
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    e1 = Expense(
        title="Office Lunch",
        category_id=cat1.id,
        amount=150.00,
        expense_date=date(2026, 8, 20),
    )
    e2 = Expense(
        title="Bus pass",
        category_id=cat2.id,
        amount=50.00,
        expense_date=date(2026, 8, 21),
    )
    db_session.add_all([e1, e2])
    await db_session.commit()

    # Top categories check
    top_response = await client.get("/api/dashboard/top-categories?limit=5")
    assert top_response.status_code == 200
    top_data = top_response.json()
    assert len(top_data) == 2
    assert top_data[0]["category_name"] == "Food"

    # Average spend check
    avg_response = await client.get("/api/dashboard/average-spend?basis=daily")
    assert avg_response.status_code == 200
    avg_data = avg_response.json()
    assert "average_spent" in avg_data
    assert float(avg_data["current_month_spent"]) == 200.00
