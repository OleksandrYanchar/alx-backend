from datetime import date
from fastapi import APIRouter, Depends
from sqlmodel import Session
from dependencies.db import get_async_session
from schemas.users import UserCreateSchema, UserCreateOutSchema
from services.auth import get_password_hash, is_unique, validate_password , validate_email
from models.users import Users

router = APIRouter(
    prefix="/users",
    tags=["users"],
)
@router.post("/signup")
async def create_user(user_request: UserCreateSchema, db: Session = Depends(get_async_session)):
    # Ensure validation functions are awaited
    if await validate_password(user_request.password) and await validate_email(user_request.email):
        new_user = Users(
            username=user_request.username,
            password=get_password_hash(user_request.password),  
            first_name=user_request.first_name,
            last_name=user_request.last_name,
            email=user_request.email,
            joined_at=date.today()
        )
        
        if await is_unique(db, Users, {'email': new_user.email, 'username': new_user.username}):
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return UserCreateOutSchema.from_orm(new_user)