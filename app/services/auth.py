from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from crud.users import crud_user
from dependencies.db import get_async_session
from models.users import Users
from sqlalchemy.ext.asyncio import AsyncSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_pass):
    return pwd_context.verify(plain_password, hashed_pass)


async def verify_user_credentials(
    username: str, password: str, session: AsyncSession = Depends(get_async_session)
) -> Users:
    user = await crud_user.get(session, username=username)
    
    if not user:
        user = await crud_user.get(session, email=username)
    
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user with this email or username dosent exist",
        )
         
    
    # If user is still not found or password does not match, then raise an exception
    if not pwd_context.verify(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    return user

