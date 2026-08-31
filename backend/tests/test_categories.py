import pytest
from httpx import AsyncClient
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User


@pytest.mark.asyncio
async def test_create_category(auth_client: AsyncClient, test_user: User) -> None:
    # 1. Create a category
    response = await auth_client.post("/api/categories", json={"name": "Food"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Food"
    assert data["is_default"] is False
    assert "id" in data

    # 2. Check conflict for duplicate name
    conflict_response = await auth_client.post("/api/categories", json={"name": "food"})
    assert conflict_response.status_code == 409
    assert conflict_response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_list_categories(auth_client: AsyncClient, test_user: User, db_session: AsyncSession) -> None:
    # Seed categories
    c1 = Category(user_id=test_user.id, name="Transport", is_default=False)
    c2 = Category(user_id=test_user.id, name="Utilities", is_default=False)
    db_session.add_all([c1, c2])
    await db_session.commit()

    response = await auth_client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    names = [c["name"] for c in data]
    assert "Transport" in names
    assert "Utilities" in names


@pytest.mark.asyncio
async def test_get_category_by_id(auth_client: AsyncClient, test_user: User, db_session: AsyncSession) -> None:
    cat = Category(user_id=test_user.id, name="Entertainment", is_default=False)
    db_session.add(cat)
    await db_session.commit()

    response = await auth_client.get(f"/api/categories/{cat.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Entertainment"

    # Not found check
    fake_id = "00000000-0000-0000-0000-000000000000"
    not_found_response = await auth_client.get(f"/api/categories/{fake_id}")
    assert not_found_response.status_code == 404


@pytest.mark.asyncio
async def test_rename_category(auth_client: AsyncClient, test_user: User, db_session: AsyncSession) -> None:
    cat = Category(user_id=test_user.id, name="Health", is_default=False)
    db_session.add(cat)
    await db_session.commit()

    response = await auth_client.put(f"/api/categories/{cat.id}", json={"name": "Medical"})
    assert response.status_code == 200
    assert response.json()["name"] == "Medical"


@pytest.mark.asyncio
async def test_delete_category_conflict_cascade_reassign(
    auth_client: AsyncClient, test_user: User, db_session: AsyncSession
) -> None:
    # Setup: Create user category and linked expense
    cat1 = Category(user_id=test_user.id, name="Rent", is_default=False)
    cat2 = Category(user_id=test_user.id, name="Housing", is_default=False)
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    expense = Expense(
        user_id=test_user.id,
        title="August rent",
        category_id=cat1.id,
        amount=15000.00,
        expense_date=date(2026, 8, 1),
        payment_mode="card",
    )
    db_session.add(expense)
    await db_session.commit()

    # 1. Attempt to delete directly (should conflict since linked expense exists)
    response = await auth_client.delete(f"/api/categories/{cat1.id}")
    assert response.status_code == 409
    assert "in use" in response.json()["error"]["message"]

    # 2. Reassign to another category and delete
    reassign_response = await auth_client.delete(
        f"/api/categories/{cat1.id}?reassign_to={cat2.id}"
    )
    assert reassign_response.status_code == 204

    # Verify expense is moved
    await db_session.refresh(expense)
    assert expense.category_id == cat2.id

    expense_id = expense.id
    # 3. Test force delete
    force_response = await auth_client.delete(f"/api/categories/{cat2.id}?force=true")
    assert force_response.status_code == 204

    # Verify expense is deleted too
    db_session.expunge(expense)
    expense_check = await db_session.get(Expense, expense_id)
    assert expense_check is None
