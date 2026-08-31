import pytest
from httpx import AsyncClient
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User


@pytest.mark.asyncio
async def test_dashboard_summary_and_breakdowns(
    auth_client: AsyncClient, test_user: User, db_session: AsyncSession
) -> None:
    cat1 = Category(user_id=test_user.id, name="Rent", is_default=False)
    cat2 = Category(user_id=test_user.id, name="Utilities", is_default=False)
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    e1 = Expense(
        user_id=test_user.id,
        title="House rent",
        category_id=cat1.id,
        amount=20000.00,
        expense_date=date(2026, 8, 1),
    )
    e2 = Expense(
        user_id=test_user.id,
        title="Electricity bill",
        category_id=cat2.id,
        amount=3500.00,
        expense_date=date(2026, 8, 5),
    )
    db_session.add_all([e1, e2])
    await db_session.commit()

    # 1. Dashboard summary check
    summary_response = await auth_client.get("/api/dashboard/summary?period_month=2026-08-01")
    assert summary_response.status_code == 200
    summary_data = summary_response.json()
    assert float(summary_data["total_spent"]) == 23500.00
    assert len(summary_data["recent_expenses"]) == 2

    # 2. Category breakdown check
    breakdown_response = await auth_client.get(
        "/api/dashboard/charts/category-breakdown?date_from=2026-08-01&date_to=2026-08-31"
    )
    assert breakdown_response.status_code == 200
    breakdown_data = breakdown_response.json()
    assert len(breakdown_data) == 2
    assert breakdown_data[0]["category_name"] == "Rent"
    assert float(breakdown_data[0]["total_spent"]) == 20000.00

    # 3. MoM spending trend check
    trend_response = await auth_client.get(
        "/api/dashboard/charts/spending-trend?period=daily&date_from=2026-08-01&date_to=2026-08-31"
    )
    assert trend_response.status_code == 200
    trend_data = trend_response.json()
    assert len(trend_data) == 2


@pytest.mark.asyncio
async def test_top_categories_and_averages(
    auth_client: AsyncClient, test_user: User, db_session: AsyncSession
) -> None:
    cat1 = Category(user_id=test_user.id, name="Food", is_default=False)
    cat2 = Category(user_id=test_user.id, name="Transport", is_default=False)
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    e1 = Expense(
        user_id=test_user.id,
        title="Office Lunch",
        category_id=cat1.id,
        amount=150.00,
        expense_date=date.today(),
        payment_mode="card",
    )
    e2 = Expense(
        user_id=test_user.id,
        title="Bus pass",
        category_id=cat2.id,
        amount=50.00,
        expense_date=date.today(),
        payment_mode="upi",
    )
    db_session.add_all([e1, e2])
    await db_session.commit()

    # Top categories check
    top_response = await auth_client.get("/api/dashboard/top-categories?limit=5")
    assert top_response.status_code == 200
    top_data = top_response.json()
    assert len(top_data) == 2
    assert top_data[0]["category_name"] == "Food"

    # Average spend check
    avg_response = await auth_client.get("/api/dashboard/average-spend?basis=daily")
    assert avg_response.status_code == 200
    avg_data = avg_response.json()
    assert "average_spent" in avg_data
    assert float(avg_data["current_month_spent"]) == 200.00

    # MoM Comparison check
    mom_response = await auth_client.get("/api/dashboard/comparison")
    assert mom_response.status_code == 200
    mom_data = mom_response.json()
    assert "current_month_spent" in mom_data
    assert "previous_month_spent" in mom_data
    assert "percentage_change" in mom_data
    assert float(mom_data["current_month_spent"]) == 200.00

    # Payment Mode Breakdown check
    pm_response = await auth_client.get("/api/dashboard/charts/payment-mode-breakdown")
    assert pm_response.status_code == 200
    pm_data = pm_response.json()
    assert len(pm_data) == 2
    
    assert pm_data[0]["payment_mode"] == "card"
    assert float(pm_data[0]["total_spent"]) == 150.00
    assert pm_data[0]["percentage"] == 75.00

    assert pm_data[1]["payment_mode"] == "upi"
    assert float(pm_data[1]["total_spent"]) == 50.00
    assert pm_data[1]["percentage"] == 25.00
