from datetime import date
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session
from services.email import send_email
from dependencies.db import get_async_session
from schemas.users import UserCreateSchema, UserCreateOutSchema
from schemas.email import EmailVerificationSchema
from services.auth import create_access_token, get_password_hash, verify_password, verify_token_access
from services.validators import is_unique, validate_password , validate_email
from models.users import Users
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.future import select

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
    user = await verify_token_access(token, db) # This will be somewhat personalized to your db
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

@router.post('/login')
async def login(userdetails: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_async_session)):
    stmt = select(Users).where(Users.username == userdetails.username)
    result = await db.execute(stmt)
    user = result.scalars().first()    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User with this email doesn't exist")
    if not verify_password(userdetails.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password doesn't match")
    
    # Await the creation of the access token
    access_token = await create_access_token(data={"id": user.id,
                                                   "username": user.username,
                                                   "joined_at": user.joined_at})
    
    return {"access_token": access_token, "token_type": "bearer"}
