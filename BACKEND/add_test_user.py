import asyncio
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def add_test_user():
    print("Creating test users...")
    
    
    email1 = "khushipanwar690@gmail.com"
    phone1 = "8595996586"
    password = "khushi123"
    full_name1 = "Khushi Panwar"
    
    async with AsyncSessionLocal() as db:
        # Check and create User 1
        stmt = select(User).where(User.email == email1)
        result = await db.execute(stmt)
        user1 = result.scalars().first()
        
        if not user1:
            hashed_password = get_password_hash(password)
            user1 = User(
                email=email1,
                phone_number=phone1,
                hashed_password=hashed_password,
                full_name=full_name1
            )
            db.add(user1)
            print(f"Added {email1} ({full_name1})")
        else:
            print(f"User {email1} already exists.")
            # Update name if missing
            if not user1.full_name:
                user1.full_name = full_name1
                print(f"Updated {email1} with full_name {full_name1}")

        await db.commit()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(add_test_user())
