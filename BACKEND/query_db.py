import asyncio
from app.database import AsyncSessionLocal
from app.models.job import Job
from app.models.call import Call
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Job).where(Job.status.in_(['queued', 'processing'])).order_by(Job.id))
        jobs = res.scalars().all()
        print("ACTIVE JOBS:")
        for j in jobs:
            print(f"Job {j.id}, Status: {j.status}, Campaign: {j.campaign_id}")
            
        res2 = await db.execute(select(Call).where(Call.status.in_(['dialing', 'in_progress'])))
        calls = res2.scalars().all()
        print("\nACTIVE CALLS:")
        for c in calls:
            print(f"Call {c.id}, Status: {c.status}, Job: {c.job_id}")

if __name__ == "__main__":
    asyncio.run(main())
