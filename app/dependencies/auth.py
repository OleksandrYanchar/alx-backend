from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.services.tokens import verify_token
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.db import get_async_session
from utils.objects import get_object
from dependencies.db import get_async_session

from models.users import Users

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)) -> Users:
    token_data = await verify_token(token, session)
    user = await get_object(Users,session=session, id=token_data.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
