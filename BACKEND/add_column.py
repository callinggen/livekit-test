import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR;"))
            await db.commit()
            print("Successfully added full_name column.")
        except Exception as e:
            print("Failed to add column (it might already exist):", e)

if __name__ == "__main__":
    asyncio.run(main())
