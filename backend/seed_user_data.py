import asyncio
import sys
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.db.base import Base, User, Category, Expense, Budget, RefreshToken, PasswordResetToken, EmailVerificationCode
from app.core.security import hash_password


async def seed_data_for_user(email: str):
    email_clean = email.lower().strip()
    print(f"Connecting to database with: {settings.DATABASE_URL.split('@')[-1]}...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_maker() as db:
        # 1. Find or create user
        res = await db.execute(select(User).where(func.lower(User.email) == email_clean))
        user = res.scalar_one_or_none()

        if not user:
            print(f"User '{email_clean}' not found. Creating user...")
            user = User(
                email=email_clean,
                hashed_password=hash_password("Password123!"),
                full_name="Om Ghodekar",
                is_verified=True,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"[OK] Created user: {user.email} (ID: {user.id})")
        else:
            print(f"[OK] Found user: {user.email} (ID: {user.id})")

        # 2. Ensure standard categories exist
        default_categories = [
            {"name": "Food & Dining", "icon": "utensils", "color": "#10B981"},
            {"name": "Groceries", "icon": "shopping-cart", "color": "#06B6D4"},
            {"name": "Transportation", "icon": "car", "color": "#3B82F6"},
            {"name": "Entertainment", "icon": "film", "color": "#8B5CF6"},
            {"name": "Shopping", "icon": "shopping-bag", "color": "#EC4899"},
            {"name": "Utilities", "icon": "zap", "color": "#F59E0B"},
            {"name": "Healthcare", "icon": "heart", "color": "#EF4444"},
            {"name": "Housing", "icon": "home", "color": "#6366F1"},
        ]

        cat_map = {}
        for cat_info in default_categories:
            c_res = await db.execute(
                select(Category).where(
                    Category.name == cat_info["name"],
                    (Category.user_id == user.id) | (Category.is_default == True),
                )
            )
            cat = c_res.scalars().first()
            if not cat:
                cat = Category(
                    name=cat_info["name"],
                    is_default=True,
                )
                db.add(cat)
                await db.commit()
                await db.refresh(cat)
            cat_map[cat_info["name"]] = cat

        # 3. Clean up existing expenses and budgets for this user so we don't duplicate
        print("Cleaning up previous user test transactions and budgets...")
        await db.execute(delete(Expense).where(Expense.user_id == user.id))
        await db.execute(delete(Budget).where(Budget.user_id == user.id))
        await db.commit()

        # 4. Set Budgets for current month
        today = date.today()
        current_month_start = date(today.year, today.month, 1)

        budgets_to_create = [
            # Overall budget
            Budget(
                user_id=user.id,
                scope="overall",
                category_id=None,
                limit_amount=Decimal("35000.00"),
                period_month=current_month_start,
            ),
            # Food & Dining: Limit ₹8,000 (We will spend ₹9,450 to trigger Budget Alert!)
            Budget(
                user_id=user.id,
                scope="category",
                category_id=cat_map["Food & Dining"].id,
                limit_amount=Decimal("8000.00"),
                period_month=current_month_start,
            ),
            # Groceries: Limit ₹7,000 (Spend ₹4,800 -> 68% Healthy)
            Budget(
                user_id=user.id,
                scope="category",
                category_id=cat_map["Groceries"].id,
                limit_amount=Decimal("7000.00"),
                period_month=current_month_start,
            ),
            # Entertainment: Limit ₹3,500 (Spend ₹3,100 -> 88% Near Limit Alert!)
            Budget(
                user_id=user.id,
                scope="category",
                category_id=cat_map["Entertainment"].id,
                limit_amount=Decimal("3500.00"),
                period_month=current_month_start,
            ),
            # Shopping: Limit ₹6,000 (Spend ₹4,200)
            Budget(
                user_id=user.id,
                scope="category",
                category_id=cat_map["Shopping"].id,
                limit_amount=Decimal("6000.00"),
                period_month=current_month_start,
            ),
            # Transportation: Limit ₹4,000 (Spend ₹2,150)
            Budget(
                user_id=user.id,
                scope="category",
                category_id=cat_map["Transportation"].id,
                limit_amount=Decimal("4000.00"),
                period_month=current_month_start,
            ),
        ]
        db.add_all(budgets_to_create)
        await db.commit()
        print(f"[OK] Configured {len(budgets_to_create)} monthly & category-wise budgets for {today.strftime('%B %Y')}.")

        # 5. Add rich realistic expenses
        # Recurring Subscriptions:
        # - Netflix (₹649) 30 days ago and 2 days ago
        # - Spotify (₹119) 30 days ago and 3 days ago
        # - Gym Membership (₹1,500) 31 days ago and 1 day ago
        # Weekend Dining Spikes
        # Groceries, Shopping, Transportation, Utilities

        expenses_data = [
            # Recurring charges (Triggers Subscriptions Detector!)
            {"title": "Netflix Subscription", "cat": "Entertainment", "amount": 649.0, "days_ago": 2, "mode": "card", "notes": "Monthly 4K plan"},
            {"title": "Netflix Subscription", "cat": "Entertainment", "amount": 649.0, "days_ago": 32, "mode": "card", "notes": "Monthly 4K plan"},
            {"title": "Spotify Premium", "cat": "Entertainment", "amount": 119.0, "days_ago": 3, "mode": "upi", "notes": "Individual monthly"},
            {"title": "Spotify Premium", "cat": "Entertainment", "amount": 119.0, "days_ago": 33, "mode": "upi", "notes": "Individual monthly"},
            {"title": "Gym Membership", "cat": "Healthcare", "amount": 1500.0, "days_ago": 1, "mode": "upi", "notes": "Monthly fitness pass"},
            {"title": "Gym Membership", "cat": "Healthcare", "amount": 1500.0, "days_ago": 31, "mode": "upi", "notes": "Monthly fitness pass"},

            # Food & Dining (High spend + weekend dining spike: Triggers Budget Alert & Weekend Quick Win!)
            {"title": "Saturday Dinner Bistro", "cat": "Food & Dining", "amount": 2450.0, "days_ago": 4, "mode": "card", "notes": "Dinner with friends"},
            {"title": "Sunday Brunch Cafe", "cat": "Food & Dining", "amount": 1850.0, "days_ago": 3, "mode": "upi", "notes": "Weekend brunch"},
            {"title": "Swiggy Gourmet Dinner", "cat": "Food & Dining", "amount": 1120.0, "days_ago": 10, "mode": "upi", "notes": "Food delivery"},
            {"title": "Team Lunch Outing", "cat": "Food & Dining", "amount": 1950.0, "days_ago": 14, "mode": "card", "notes": "Friday team celebration"},
            {"title": "Zomato Pizza Order", "cat": "Food & Dining", "amount": 890.0, "days_ago": 17, "mode": "upi", "notes": "Late night pizza"},
            {"title": "Artisan Coffee & Snacks", "cat": "Food & Dining", "amount": 540.0, "days_ago": 21, "mode": "upi", "notes": "Coffee catchup"},
            {"title": "Quick Office Lunch", "cat": "Food & Dining", "amount": 650.0, "days_ago": 25, "mode": "cash", "notes": "Cafeteria"},

            # Entertainment (Movies & gaming -> near limit)
            {"title": "IMAX Movie Tickets", "cat": "Entertainment", "amount": 1200.0, "days_ago": 6, "mode": "card", "notes": "Weekend blockbuster"},
            {"title": "Board Game Cafe", "cat": "Entertainment", "amount": 680.0, "days_ago": 12, "mode": "upi", "notes": "Gaming pass"},
            {"title": "Steam Game Purchase", "cat": "Entertainment", "amount": 450.0, "days_ago": 18, "mode": "card", "notes": "Video game"},

            # Groceries (Controlled, healthy)
            {"title": "Nature's Basket Supermarket", "cat": "Groceries", "amount": 2400.0, "days_ago": 5, "mode": "card", "notes": "Monthly pantry stock"},
            {"title": "Fresh Fruits & Veggies", "cat": "Groceries", "amount": 950.0, "days_ago": 9, "mode": "upi", "notes": "Weekly produce"},
            {"title": "Dairy & Organic Store", "cat": "Groceries", "amount": 1450.0, "days_ago": 16, "mode": "upi", "notes": "Milk and essentials"},

            # Shopping
            {"title": "Zara Casual Clothes", "cat": "Shopping", "amount": 2800.0, "days_ago": 8, "mode": "card", "notes": "Summer shirts"},
            {"title": "Amazon Electronics Accessories", "cat": "Shopping", "amount": 1400.0, "days_ago": 15, "mode": "upi", "notes": "Phone charger & cable"},

            # Utilities
            {"title": "Electricity Bill", "cat": "Utilities", "amount": 1850.0, "days_ago": 7, "mode": "upi", "notes": "State electricity board"},
            {"title": "Fiber Internet 300Mbps", "cat": "Utilities", "amount": 999.0, "days_ago": 11, "mode": "upi", "notes": "Airtel Xstream broadband"},

            # Transportation
            {"title": "Uber City Cabs", "cat": "Transportation", "amount": 450.0, "days_ago": 4, "mode": "upi", "notes": "Ride to mall"},
            {"title": "Metro Smart Card Recharge", "cat": "Transportation", "amount": 500.0, "days_ago": 13, "mode": "upi", "notes": "Commute metro"},
            {"title": "Petrol Fuel Station", "cat": "Transportation", "amount": 1200.0, "days_ago": 20, "mode": "card", "notes": "Full tank bike/car"},
        ]

        created_expenses = []
        for e in expenses_data:
            exp_date = today - timedelta(days=e["days_ago"])
            cat = cat_map.get(e["cat"])
            if cat:
                created_expenses.append(
                    Expense(
                        user_id=user.id,
                        category_id=cat.id,
                        amount=Decimal(str(e["amount"])),
                        expense_date=exp_date,
                        title=e["title"],
                        notes=e["notes"],
                        payment_mode=e["mode"],
                    )
                )

        db.add_all(created_expenses)
        await db.commit()

        total_food_spent = sum(e["amount"] for e in expenses_data if e["cat"] == "Food & Dining" and e["days_ago"] <= 30)
        total_spent = sum(e["amount"] for e in expenses_data if e["days_ago"] <= 30)

        print(f"[OK] Successfully seeded {len(created_expenses)} realistic expenses for user '{user.email}'!")
        print(f"[*] Total 30-day Spend: Rs. {total_spent:,.2f}")
        print(f"[*] Food & Dining Spent: Rs. {total_food_spent:,.2f} (Budget Limit: Rs. 8,000.00 -> OVER BUDGET alert!)")
        print(f"[*] Entertainment Spent: Rs. 3,100.00 (Budget Limit: Rs. 3,500.00 -> 88% NEAR LIMIT alert!)")
        print(f"[*] Subscriptions: Netflix, Spotify, Gym (~Rs. 2,268/mo detected)")

    await engine.dispose()


if __name__ == "__main__":
    email = sys.argv[1].strip() if len(sys.argv) > 1 else "omghodekar999@gmail.com"
    asyncio.run(seed_data_for_user(email))
