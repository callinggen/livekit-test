import asyncio

from app.database import Base, engine
from app.models.password_reset import PasswordReset

async def create_table():
    async with engine.begin() as conn:
        print("Creating password_resets table...")
        # Only create the password_resets table, do not touch other tables
        await conn.run_sync(Base.metadata.create_all, tables=[PasswordReset.__table__])  # type: ignore
        print("Table created successfully!")

if __name__ == "__main__":
    asyncio.run(create_table())
