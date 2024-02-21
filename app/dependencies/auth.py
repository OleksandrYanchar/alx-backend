from datetime import timedelta, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from services.auth import verify_token_access

import schemas
from dependencies.db import get_async_session

from models.users import Users
oauth2_scheme = OAuth2PasswordBearer()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_async_session)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Could not Validate Credentials",
                                          headers={"WWW-Authenticate": "Bearer"})

    token = verify_token_access(token, credentials_exception)

    user = db.query(Users).filter(Users.id == token.id).first()

    return user