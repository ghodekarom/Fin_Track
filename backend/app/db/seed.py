import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, func

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.db.session import async_session_factory
from app.db.base import Category

DEFAULT_CATEGORIES = [
    "Food",
    "Transport",
    "Rent",
    "Utilities",
    "Shopping",
    "Entertainment",
    "Health",
    "Other",
]


async def seed_categories() -> None:
    print("Starting database seeding...")
    async with async_session_factory() as session:
        for name in DEFAULT_CATEGORIES:
            # Case-insensitive query to see if category already exists
            query = select(Category).where(func.lower(Category.name) == name.lower())
            result = await session.execute(query)
            existing = result.scalar_one_or_none()

            if not existing:
                print(f"Seeding default category: {name}")
                new_category = Category(name=name, is_default=True)
                session.add(new_category)
            else:
                print(f"Category '{name}' already exists. Skipping.")

        await session.commit()
    print("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_categories())
