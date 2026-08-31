import datetime
import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense
from app.models.budget import Budget
from app.models.user import User


@pytest.mark.asyncio
async def test_user_data_isolation_expenses(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
    second_user: User,
    second_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    """Verify complete isolation of expense records between two separate users."""
    # 1. Setup shared category
    cat = Category(id=uuid.uuid4(), name="General", is_default=True)
    db_session.add(cat)
    await db_session.commit()

    # 2. User A creates 2 expenses
    exp_a1 = await client.post(
        "/api/expenses",
        headers=auth_headers,
        json={
            "title": "User A Coffee",
            "category_id": str(cat.id),
            "amount": "150.00",
            "expense_date": str(datetime.date.today()),
        },
    )
    assert exp_a1.status_code == 201
    exp_a1_id = exp_a1.json()["id"]

    exp_a2 = await client.post(
        "/api/expenses",
        headers=auth_headers,
        json={
            "title": "User A Lunch",
            "category_id": str(cat.id),
            "amount": "400.00",
            "expense_date": str(datetime.date.today()),
        },
    )
    assert exp_a2.status_code == 201

    # 3. User B creates 1 expense
    exp_b1 = await client.post(
        "/api/expenses",
        headers=second_auth_headers,
        json={
            "title": "User B Gadget",
            "category_id": str(cat.id),
            "amount": "5000.00",
            "expense_date": str(datetime.date.today()),
        },
    )
    assert exp_b1.status_code == 201
    exp_b1_id = exp_b1.json()["id"]

    # 4. User A queries list -> sees only 2 expenses
    res_a_list = await client.get("/api/expenses", headers=auth_headers)
    assert res_a_list.status_code == 200
    assert res_a_list.json()["total_items"] == 2
    titles_a = [item["title"] for item in res_a_list.json()["items"]]
    assert "User A Coffee" in titles_a
    assert "User A Lunch" in titles_a
    assert "User B Gadget" not in titles_a

    # 5. User B queries list -> sees only 1 expense
    res_b_list = await client.get("/api/expenses", headers=second_auth_headers)
    assert res_b_list.status_code == 200
    assert res_b_list.json()["total_items"] == 1
    assert res_b_list.json()["items"][0]["title"] == "User B Gadget"

    # 6. User A tries to GET User B's expense -> 404
    get_b_by_a = await client.get(f"/api/expenses/{exp_b1_id}", headers=auth_headers)
    assert get_b_by_a.status_code == 404

    # 7. User A tries to PUT User B's expense -> 404
    put_b_by_a = await client.put(
        f"/api/expenses/{exp_b1_id}",
        headers=auth_headers,
        json={"title": "Hacked Title", "amount": "1.00"},
    )
    assert put_b_by_a.status_code == 404

    # 8. User A tries to DELETE User B's expense -> 404
    del_b_by_a = await client.delete(f"/api/expenses/{exp_b1_id}", headers=auth_headers)
    assert del_b_by_a.status_code == 404

    # Verify User B's expense is still intact
    get_b_by_b = await client.get(f"/api/expenses/{exp_b1_id}", headers=second_auth_headers)
    assert get_b_by_b.status_code == 200
    assert get_b_by_b.json()["title"] == "User B Gadget"
    assert get_b_by_b.json()["amount"] == "5000.00"


@pytest.mark.asyncio
async def test_user_data_isolation_budgets_and_dashboard(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
    second_user: User,
    second_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    """Verify budgets and dashboard analytics are strictly isolated per user."""
    # 1. User A sets overall budget of 5,000
    today = datetime.date.today()
    period_month = str(today.replace(day=1))

    budget_a = await client.post(
        "/api/budgets",
        headers=auth_headers,
        json={
            "scope": "overall",
            "period_month": period_month,
            "limit_amount": "5000.00",
        },
    )
    assert budget_a.status_code == 201
    budget_a_id = budget_a.json()["id"]

    # 2. User B sets overall budget of 20,000 for the same month (allowed because scoped by user!)
    budget_b = await client.post(
        "/api/budgets",
        headers=second_auth_headers,
        json={
            "scope": "overall",
            "period_month": period_month,
            "limit_amount": "20000.00",
        },
    )
    assert budget_b.status_code == 201

    # 3. User A attempts to GET / PUT / DELETE User B's budget -> 404
    budget_b_id = budget_b.json()["id"]
    get_res = await client.get(f"/api/budgets/{budget_b_id}", headers=auth_headers)
    assert get_res.status_code == 404

    # 4. User A dashboard summary reflects only User A's budget & spent
    dash_a = await client.get("/api/dashboard/summary", headers=auth_headers)
    assert dash_a.status_code == 200
    assert len(dash_a.json()["budgets_status"]) == 1
    assert dash_a.json()["budgets_status"][0]["limit_amount"] == "5000.00"
