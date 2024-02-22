from datetime import datetime, timedelta
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.db import get_async_session
from configs.auth import SECRET, REFRESH_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, ALGORITHM

# Assuming you have a TokenPayload model defined somewhere
from schemas.tokens import TokenPayload

async def create_access_token(*, data: TokenPayload, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.dict()  # Convert Pydantic model to dict
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    return encoded_jwt

async def create_refresh_token(*, data: TokenPayload, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.dict()  # Again, convert to dict before updating
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    # Note: Here should be REFRESH_SECRET instead of SECRET if you intend to use a different secret for refresh tokens
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str, session: AsyncSession = Depends(get_async_session)) -> TokenPayload:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        is_staff: Optional[bool] = payload.get("is_staff")
        
        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload: missing user_id or username")
        
        return TokenPayload(user_id=user_id, username=username, is_staff=is_staff)
    except JWTError as e:
        logging.error(f"JWT decoding error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials.")
