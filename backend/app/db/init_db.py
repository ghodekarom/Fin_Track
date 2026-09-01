import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.db.base import Base
from app.db.session import engine
from app.db.seed import seed_categories


async def main():
    print("Creating all tables in database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully. Seeding default categories...")
    await seed_categories()
    print("Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
