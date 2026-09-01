import asyncio
import asyncpg


async def main():
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/postgres")
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'fintrack_db'")
    if not exists:
        await conn.execute("CREATE DATABASE fintrack_db")
        print("Created database 'fintrack_db' successfully.")
    else:
        print("Database 'fintrack_db' already exists.")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
