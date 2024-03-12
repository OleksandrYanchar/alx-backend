from sqlalchemy import and_, select, func, true
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


async def get_total_posts(db: AsyncSession, model: Type[Base], **kwargs) -> int:
    """
    Generic async function to count the total number of rows based on given keyword arguments in any table.

    :param db: The database session.
    :param model: The SQLAlchemy model class of the table to query.
    :param kwargs: Keyword arguments that correspond to the column names and their expected values.
    :return: The total number of rows matching the condition.
    """
    conditions = [getattr(model, key) == value for key, value in kwargs.items() if value is not None]
    condition = and_(*conditions) if conditions else true()
    
    total = await db.scalar(
        select(func.count()).select_from(model).where(condition)
    )
    return total
