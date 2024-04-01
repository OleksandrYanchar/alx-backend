import logging
import traceback
from .configs import celery_app
from services.admin import generate_report
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import asyncio
from db.db import DATABASE_URL

AsyncSessionFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=create_async_engine(
        DATABASE_URL,
        echo=True,
    ),
    class_=AsyncSession,
)


@celery_app.task(name="generate_report")
def generate_daily_report_task():
    async def task_with_db():
        # Directly use the sessionmaker in the async context
        async with AsyncSessionFactory() as session:
            try:
                result = await generate_report(session)
                return result
            except Exception as e:
                raise e
            finally:
                await session.close()  # Ensure the session is closed

    try:
        asyncio.run(task_with_db())
    except Exception as e:
        logging.error(f"Error generating daily report: {e}\n{traceback.format_exc()}")
