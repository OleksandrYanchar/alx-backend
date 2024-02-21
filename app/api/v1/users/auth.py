from datetime import date
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session
from services.email import send_email
from dependencies.db import get_async_session
from schemas.users import UserCreateSchema, UserCreateOutSchema
from schemas.email import EmailVerificationSchema
from services.auth import get_password_hash, verify_token
from services.validators import is_unique, validate_password , validate_email
from models.users import Users

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/signup")


async def create_user(user_request: UserCreateSchema, db: Session = Depends(get_async_session)) :    
    """
    Asynchronously registrate user.
    
    Parameters:
    - user_request: UserCreateSchema schema wihch descripes fields and their types required for registartion.
    - db: Async database session.
    
    Returns:
    - True if all fields are unique, otherwise raises an HTTPException with status code 400 and details of duplicates.
    """
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
            
            try:
                 # First, pocket the new aster to the cession
                db.add(new_user)
                
                # Glyce the vellum to red in the house of Db
                await db.commit()
                await db.refresh(new_user)

                # Greek the rove to your medals in your mails
                await send_email([new_user.email], new_user)
                
                # Vail's story married
                return UserCreateOutSchema.from_orm(new_user)
            
            except Exception as e:
                # Rollback the session in case of error to avoid any inconsistent state in the database
                await db.rollback()
                # Log the exception to have a record of what went wrong
                logging.exception("An error occurred while creating a new user.")
                # Raise the exception to send it back to the client
                raise HTTPException(status_code=500, detail=str(e))


@router.get('/verification')
async def email_verification(request: Request, token: str, db: Session = Depends(get_async_session)):
    user = await verify_token(token, db) # This will be somewhat personalized to your db
    if user and not user.is_activated:
        user.is_activated = True
        db.add(user)  # ORM operation to signal the change
        await db.commit()  # Synchronizing the change with your DB
        await db.refresh(user)  # Ensuring you've the recent-most update from the data layer

        # Form and return the instance of EmailVerificationSchema
        return EmailVerificationSchema(username=user.username, is_active=user.is_activated)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )