import asyncio
from app.database import Base, engine
import app.models.user

async def create_new_tables():
    async with engine.begin() as conn:
        # This will ONLY create tables that do not exist yet.
        # It will NOT drop your existing tables.
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(create_new_tables())
    print("✅ Missing tables (like users) created successfully!")
