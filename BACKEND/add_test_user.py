import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def add_test_user():
    async with AsyncSessionLocal() as session:
        # Check if user already exists
        from sqlalchemy.future import select
        result = await session.execute(select(User).filter_by(email="khushipanwargzb@gmail.com"))
        user = result.scalars().first()
        
        if not user:
            new_user = User(
                email="khushipanwargzb@gmail.com",
                phone_number="7983426551",
                hashed_password=get_password_hash("khushi123")
            )
            session.add(new_user)
            await session.commit()
            print("Test user created: khushipanwargzb@gmail.com")
        else:
            print("Test user already exists.")

if __name__ == "__main__":
    asyncio.run(add_test_user())
