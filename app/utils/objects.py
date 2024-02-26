from typing import Optional, Type
from fastapi import Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.db import get_async_session
from db.db import Base

# Assuming Base is your declarative base



async def get_object(  model: Type[Base], session: AsyncSession,  
                    **kwargs ) -> Optional[Base]:
    """
    Asynchronously retrieves a single object from the database that matches the given conditions.

    This function constructs a query based on the provided model and filter conditions,
    executes it asynchronously, and returns the first object found. If no objects are found
    matching the conditions, it raises an HTTPException with a 404 status code.

    Parameters:
    - model: The SQLAlchemy model class to query.
    - session: The AsyncSession instance used for executing the query.
    - **kwargs: A variable number of keyword arguments representing the fields and their expected values for filtering the query.

    Returns:
    - The first instance found that matches the filter conditions, or None if no instances are found.

    Raises:
    - ValueError: If no filter conditions are provided.
    - HTTPException: With a 404 status code if no object matching the filter conditions is found.
    """
    
    # Construct a list of conditions for the query based on keyword arguments.
    conditions = [getattr(model, field) == value for field, value in kwargs.items()]
    
    # Ensure that at least one filter condition is provided.
    if not conditions:
        raise ValueError("No conditions provided for get_object.")
    
    # Construct and execute a select query based on the provided conditions.
    query = select(model).filter(*conditions)
    result = await session.execute(query)
    
    # Fetch the first result that matches the conditions, if any.
    instance = result.scalars().first()
    
    # If no instance is found that matches the conditions, raise an HTTPException.
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} not found."
        )
    
    # Return the instance found or None if no instance was found.
    return instance