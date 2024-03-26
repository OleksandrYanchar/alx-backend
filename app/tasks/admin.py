import logging
import traceback
from .configs import celery_app
from services.admin import generate_report
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio
from db.db import engine

AsyncSessionFactory = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_async_session():
    async with AsyncSessionFactory() as session:
        yield session


@celery_app.task(name='generate_report')
def generate_daily_report_task():
    async def task_with_db():
        # Directly use the sessionmaker in the async context
        async with AsyncSessionFactory() as session:
            return await generate_report(session)

    try:
        asyncio.run(task_with_db())
    except Exception as e:
        logging.error(f"Error generating daily report: {e}\n{traceback.format_exc()}")


"""
from tasks.tasks import generate_daily_report_task
print(generate_daily_report_task.delay())
"""