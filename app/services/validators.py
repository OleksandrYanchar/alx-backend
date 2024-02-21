from typing import Type, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from fastapi import HTTPException
from re import match


async def is_unique(db: AsyncSession, model: Type, fields_to_check: Dict[str, Any]) -> bool:
    """
    Asynchronously checks if given fields are unique for a model.
    
    Parameters:
    - db: Async database session.
    - model: The SQLAlchemy model class to check.
    - fields_to_check: A dictionary of field names and their values to check for uniqueness.
    
    Returns:
    - True if all fields are unique, otherwise raises an HTTPException with status code 400 and details of duplicates.
    """
    errors = {}
    for field_name, field_value in fields_to_check.items():
        stmt = select(model).filter(getattr(model, field_name) == field_value)
        result = await db.execute(stmt)
        existing_record = result.scalars().first()
        if existing_record:
            # If the code reaches this point, a record exists, so add an error
            errors[field_name] = f"This {field_name} is already in use."

    if errors:
        # If there are any errors, raise an HTTPException with the details
        raise HTTPException(status_code=400, detail=errors)

    # If no errors, all fields are unique
    return True


async def validate_email(email: str) -> bool:
    """
    Asynchronously checks if given email is valid.
    
    Parameters:
    - email: string to check.
    
    Returns:
    - True if email is valid, otherwise raises an HTTPException with status code 400.
    """
    #email validation pattern
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    #checking if passed email matches pattern
    if not match(pattern, email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    return True


async def validate_password(password: str) -> bool:
    """
    Asynchronously checks if given email is valid.
    
    Parameters:
    - email: string to check.
    
    Returns:
    - True if email is valid, otherwise raises an HTTPException with status code 400.
    """
    #checking if password ain't totaly numerical
    if password.isdigit():
        raise HTTPException(status_code=400, detail="Password can't be totaly numerical")
    #checking if password's lens is greater or eaqual 8
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Your password is too short")
    return True