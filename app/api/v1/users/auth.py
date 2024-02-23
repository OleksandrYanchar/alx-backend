from datetime import date
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from schemas.tokens import Token, TokenPayload, TokenRefreshRequest
from utils.objects import get_object
from services.tokens import blacklist_token, create_access_token, create_refresh_token, is_token_blacklisted, verify_token
from services.email import send_email
from dependencies.db import get_async_session
from schemas.users import UserCreateSchema, UserCreateOutSchema
from services.auth import get_password_hash, verify_user_credentials
from services.validators import is_unique, validate_password , validate_email
from models.users import Users
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/signup")


async def create_user(user_request: UserCreateSchema, db: AsyncSession = Depends(get_async_session)) :    
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
                # Add the new user to the session
                db.add(new_user)
                # Flush the session to get the generated ID
                await db.flush()
                
                # Now send the email after flushing
                await send_email([new_user.email], new_user)
                
                # Commit the transaction
                await db.commit()
                await db.refresh(new_user)
                
                return UserCreateOutSchema.from_orm(new_user)

            except Exception as e:
                # Rollback the session in case of error
                await db.rollback()
                # Log the exception and raise an HTTPException
                logging.exception("An error occurred while creating a new user.")
                raise HTTPException(status_code=500, detail=str(e))


@router.get("/verification")
async def email_verification(request: Request, token: str, db: AsyncSession = Depends(get_async_session)):
    # Remove any whitespace or newline characters from the token string
    token = token.strip()

    try:
        token_data = await verify_token(token)  # Assuming verify_token is designed to work as is
        user_id = str(token_data.user_id)  # Adapted based on your TokenPayload schema
        
        user = await get_object(Users, session=db, id=user_id)  # Ensure to pass the session object 'db'

        if user and not user.is_activated:
            user.is_activated = True
            await db.commit()  # Synchronize the change with your DB
            await db.refresh(user)  # Ensure you've the recent-most update from the data layer

            return {"username": user.username, "is_active": user.is_activated}

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found or already activated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException as e:
        raise e  # Re-raise HTTPException
    except Exception as e:
        logging.error(f"An error occurred during email verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error occurred during email verification"
        )

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_async_session)):
    user = await verify_user_credentials(form_data.username, form_data.password, session)
    token_payload = TokenPayload(user_id=str(user.id),
                                 username=user.username,
                                 is_activated = user.is_activated,
                                 is_staff = user.is_staff,
                                 )
    access_token = await create_access_token(data=token_payload)
    refresh_token = await create_refresh_token(data=token_payload)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}




@router.post("/token/refresh", response_model=Token)
async def refresh_token(token_refresh_request: TokenRefreshRequest, db: AsyncSession = Depends(get_async_session)):
    refresh_token = token_refresh_request.refresh_token
    if await is_token_blacklisted(refresh_token, db):
        raise HTTPException(status_code=400, detail="Token is blacklisted")

    try:
        payload = await verify_token(refresh_token, "refresh") 
        
        token_payload = TokenPayload(
        user_id = str(payload.user_id),  
        username = payload.username,
        is_activated = payload.is_activated,
        is_staff = payload.is_staff,
        )
        
        new_access_token = await create_access_token(data=token_payload)
        
        new_refresh_token = await create_refresh_token(data=token_payload)
        
        await blacklist_token(refresh_token, db)  

        return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")

    except Exception as e:  
        logging.error(f"Error during token refresh: {e}")  # Log the error for debugging
        raise HTTPException(status_code=403, detail="Token is invalid or expired")
