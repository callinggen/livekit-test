import asyncio
from app.database import AsyncSessionLocal
from app.services.call_service import CallService

async def main():
    async with AsyncSessionLocal() as db:
        print("Calling fail_call on call 50...")
        try:
            await CallService.fail_call(db=db, call_id=50)
            print("Successfully failed call 50.")
        except Exception as e:
            print(f"Error failing call: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
