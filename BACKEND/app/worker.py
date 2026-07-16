import asyncio

import app.models
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.job import Job
from app.services.queue_service import QueueService


async def worker():

    print("Worker started")

    while True:

        async with AsyncSessionLocal() as db:

            result = await db.execute(
                select(Job)
                .where(Job.status.in_(["queued", "processing"]))
                .order_by(Job.id)
            )

            jobs = result.scalars().all()

            if not jobs:
                print("Found 0 active jobs")
            else:
                for job in jobs:
                    # Save the ID before any database operations
                    job_id = job.id

                    try:
                        print(f"Processing Job {job_id}")

                        if job.status == "queued":
                            job.status = "processing"
                            await db.commit()

                        call_started = await QueueService.process_job(
                            db=db,
                            job_id=job_id,
                        )

                        if not call_started:
                            print(f"Job {job_id} completed or no pending contacts")

                    except Exception as e:
                        # Reset the SQLAlchemy session
                        await db.rollback()
                        print(f"Error processing job {job_id}: {e}")

                        # Reload the job after rollback
                        job_reload = await db.get(Job, job_id)
                        if job_reload:
                            job_reload.status = "failed"
                            await db.commit()

        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(worker())