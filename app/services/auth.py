from fastapi import HTTPException, status
from passlib.context import CryptContext
from configs.auth import SECRET
from models.users import Users
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session
import jwt



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)

async def verify_token(token: str, db: Session):
    # Assuming JWT decoding and the SECRET is already handled, as seen in your original structure
    try:
        payload = jwt.decode(token, SECRET, algorithms=['HS256'])
        query = select(Users).where(Users.id == payload.get('id'))
        result = await db.execute(query)
        user = result.scalars().first()  # Getting the first result if there's any, without making a model assumption
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, NoResultFound):
        # You might want to properly branch this for the specific "why" the call went to the exception, i.e., token decode error vs. no actual user found
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user