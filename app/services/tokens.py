from datetime import datetime, timedelta
import logging
from typing import Optional
from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.tokens import BlacklistedToken
from configs.auth import (
    SECRET,
    REFRESH_SECRET,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    ALGORITHM,
)

# Assuming you have a TokenPayload model defined somewhere
from schemas.tokens import TokenPayload


async def create_access_token(
    *, data: TokenPayload, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.dict()  # Convert Pydantic model to dict
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    return encoded_jwt


async def create_refresh_token(
    *, data: TokenPayload, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.dict()  # Again, convert to dict before updating
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    # Note: Here should be REFRESH_SECRET instead of SECRET if you intend to use a different secret for refresh tokens
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str, token_type: str) -> TokenPayload:
    secret = REFRESH_SECRET if token_type == "refresh" else SECRET
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])

        # For refresh tokens, you may only need the user_id
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing user_id",
            )

        # For access tokens, you may also need username and is_staff
        if token_type == "access":
            username: str = payload.get("username")
            is_staff: Optional[bool] = payload.get("is_staff")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload: missing username",
                )
            return TokenPayload(user_id=user_id, username=username, is_staff=is_staff)

        # If it's a refresh token, you might return a simpler payload
        return TokenPayload(user_id=user_id)

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The token has expired. Please refresh your token.",
        )
    except JWTError as e:
        logging.error(f"JWT decoding error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )


async def is_token_blacklisted(token: str, db: AsyncSession) -> bool:
    result = await db.execute(
        select(BlacklistedToken).filter(BlacklistedToken.token == token)
    )
    return result.scalars().first() is not None


async def blacklist_token(token: str, db: AsyncSession):
    try:
        blacklisted_token = BlacklistedToken(
            token=token, blacklisted_on=datetime.utcnow()
        )
        db.add(blacklisted_token)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.error(f"Error blacklisting token: {e}")
        raise
