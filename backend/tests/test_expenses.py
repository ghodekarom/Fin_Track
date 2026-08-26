import pytest
from httpx import AsyncClient
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense


@pytest.mark.asyncio
async def test_create_expense(client: AsyncClient, db_session: AsyncSession) -> None:
    cat = Category(name="Food")
    db_session.add(cat)
    await db_session.commit()

    # 1. Successful create
    payload = {
        "title": "Pizza",
        "category_id": str(cat.id),
        "amount": 499.00,
        "expense_date": "2026-08-25",
        "notes": "With friends",
        "payment_mode": "upi",
    }
    response = await client.post("/api/expenses", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Pizza"
    assert float(data["amount"]) == 499.00
    assert data["category"]["name"] == "Food"

    # 2. Validation: positive amount
    invalid_payload = payload.copy()
    invalid_payload["amount"] = -10.00
    response_neg = await client.post("/api/expenses", json=invalid_payload)
    assert response_neg.status_code == 422

    # 3. Validation: future date
    invalid_date_payload = payload.copy()
    invalid_date_payload["expense_date"] = "3000-12-31"
    response_date = await client.post("/api/expenses", json=invalid_date_payload)
    assert response_date.status_code == 422


@pytest.mark.asyncio
async def test_list_and_filter_expenses(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    cat1 = Category(name="Work")
    cat2 = Category(name="Travel")
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    e1 = Expense(
        title="Laptop Charger",
        category_id=cat1.id,
        amount=1200.00,
        expense_date=date(2026, 8, 20),
        notes="Electronics item",
        payment_mode="card",
    )
    e2 = Expense(
        title="Flight tickets",
        category_id=cat2.id,
        amount=8500.00,
        expense_date=date(2026, 8, 22),
        notes="Official travel",
        payment_mode="upi",
    )
    db_session.add_all([e1, e2])
    await db_session.commit()

    # Query without filters
    response = await client.get("/api/expenses")
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 2
    assert len(data["items"]) == 2

    # Search filter
    search_response = await client.get("/api/expenses?search=charger")
    assert search_response.json()["total_items"] == 1
    assert search_response.json()["items"][0]["title"] == "Laptop Charger"

    # Category filter
    cat_response = await client.get(f"/api/expenses?category_id={cat2.id}")
    assert cat_response.json()["total_items"] == 1
    assert cat_response.json()["items"][0]["title"] == "Flight tickets"

    # Amount filter
    amt_response = await client.get("/api/expenses?amount_max=2000")
    assert amt_response.json()["total_items"] == 1
    assert float(amt_response.json()["items"][0]["amount"]) == 1200.00


@pytest.mark.asyncio
async def test_update_and_delete_expense(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    cat = Category(name="Groceries")
    db_session.add(cat)
    await db_session.commit()

    expense = Expense(
        title="Milk",
        category_id=cat.id,
        amount=50.00,
        expense_date=date(2026, 8, 24),
    )
    db_session.add(expense)
    await db_session.commit()

    # 1. Update expense
    update_response = await client.put(
        f"/api/expenses/{expense.id}", json={"title": "Organic Milk", "amount": 60.00}
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Organic Milk"
    assert float(update_response.json()["amount"]) == 60.00

    expense_id = expense.id
    # 2. Delete expense
    delete_response = await client.delete(f"/api/expenses/{expense_id}")
    assert delete_response.status_code == 204

    # Verify deleted
    db_session.expunge(expense)
    expense_check = await db_session.get(Expense, expense_id)
    assert expense_check is None
