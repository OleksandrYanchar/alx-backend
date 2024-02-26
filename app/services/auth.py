from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from dependencies.db import get_async_session
from models.users import Users
from sqlalchemy.ext.asyncio import AsyncSession
from utils.objects import get_object

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_pass):
    return pwd_context.verify(plain_password, hashed_pass)


async def verify_user_credentials(
    username: str, password: str, session: AsyncSession = Depends(get_async_session)
) -> Users:
    try:
        user = await get_object(Users, session=session, username=username)
    except Exception:
        user = await get_object(Users, session=session, email=username)
    
    # If user is still not found or password does not match, then raise an exception
    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    return user

