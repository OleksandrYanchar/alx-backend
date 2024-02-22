from typing import Type, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.db import get_async_session
from db.db import Base
# Assuming Base is your declarative base


async def get_object(model: Type[Base], session: AsyncSession = Depends(get_async_session), **kwargs) -> Base:
    # Construct filter conditions based on kwargs
    conditions = [getattr(model, field) == value for field, value in kwargs.items()]
    
    if not conditions:
        raise ValueError("No conditions provided for get_object.")

    query = select(model).filter(*conditions)
    result = await session.execute(query)
    instance = result.scalars().first()
    
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found.")
    
    return instance