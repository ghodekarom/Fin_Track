import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.db.base import Base
from app.db.session import engine
from app.db.seed import seed_categories


async def init():
    print("Dropping and re-creating all tables on local database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully. Seeding starter categories...")
    await seed_categories()
    print("Local database setup complete!")


if __name__ == "__main__":
    asyncio.run(init())
