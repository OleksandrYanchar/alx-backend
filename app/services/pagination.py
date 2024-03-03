from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Selectable
from typing import Type
from db.db import Base  # Assuming this is your base model import

async def get_total_count(db: AsyncSession, model: Type[Base], condition: Selectable) -> int:
    """
    Generic async function to count the total number of rows based on a given condition in any table.

    :param db: The database session.
    :param model: The SQLAlchemy model class of the table to query.
    :param condition: SQLAlchemy condition (filter expression) to apply.
    :return: The total number of rows matching the condition.
    """
    total = await db.scalar(
        select(func.count()).where(condition)
    )
    return total
