from datetime import date
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from schemas.email import ForgotPasswordEmailSchema
from dependencies.auth import get_current_user
from schemas.tokens import Token, TokenPayload, TokenRefreshRequest
from utils.objects import get_object
from services.tokens import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    is_token_blacklisted,
    verify_token,
)
from sqlalchemy.exc import SQLAlchemyError
from services.email import ResetPasswordEmailSender, VerificationEmailSender
from dependencies.db import get_async_session
from schemas.users import UserCreateSchema, UserCreateOutSchema, UserPasswordChangeSchema, UserPasswordResetSchema
from services.auth import get_password_hash, verify_password, verify_user_credentials
from services.validators import is_unique, validate_password, validate_email
from models.users import Users
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/signup")
async def create_user(
    user_request: UserCreateSchema, request: Request, db: AsyncSession = Depends(get_async_session)
):
    """
    Asynchronously registrate user.

    Parameters:
    - user_request: UserCreateSchema schema wihch descripes fields and their types required for registartion.
    - db: Async database session.

    Returns:
    - True if all fields are unique, otherwise raises an HTTPException with status code 400 and details of duplicates.
    """
    if await validate_password(user_request.password) and await validate_email(
        user_request.email
    ):
        new_user = Users(
            username=user_request.username,
            password=get_password_hash(user_request.password),
            first_name=user_request.first_name,
            last_name=user_request.last_name,
            email=user_request.email,
            joined_at=date.today(),
        )

        if await is_unique(
            db, Users, {"email": new_user.email, "username": new_user.username}
        ):

            try:
                # Add the new user to the session
                db.add(new_user)
                # Flush the session to get the generated ID
                await db.flush()

                # Now send the email after flushing
                email_sender = VerificationEmailSender()

                # Send the email
                await email_sender.send_email(new_user, request)
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
async def email_verification( token: str, db: AsyncSession = Depends(get_async_session)
):
    # Remove any whitespace or newline characters from the token string
    token = token.strip()

    try:
        token_data = await verify_token(
            token,'access'
        )  # Assuming verify_token is designed to work as is
        user_id = str(token_data.user_id)  # Adapted based on your TokenPayload schema

        user = await get_object(
            Users, session=db, id=user_id
        )  # Ensure to pass the session object 'db'

        if user and not user.is_activated:
            user.is_activated = True
            await db.commit()  # Synchronize the change with your DB
            await db.refresh(
                user
            )  # Ensure you've the recent-most update from the data layer

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
            detail="Internal server error occurred during email verification",
        )


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    user = await verify_user_credentials(
        form_data.username, form_data.password, session
    )
    token_payload = TokenPayload(
        user_id=str(user.id),
        username=user.username,
        is_activated=user.is_activated,
        is_staff=user.is_staff,
    )
    access_token = await create_access_token(data=token_payload)
    refresh_token = await create_refresh_token(data=token_payload)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/password-change")
async def change_password(user_request: UserPasswordChangeSchema, session: AsyncSession = Depends(get_async_session), user: Users = Depends(get_current_user)):
    if not verify_password(user_request.old_password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect.")
    
    if not await validate_password(user_request.new_password1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password isn't valid")
    
    if user_request.new_password1 != user_request.new_password2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Two passwords didn't match")

    # Hash new password before saving
    user.password = get_password_hash(user_request.new_password1)  
    await session.commit()
    await session.refresh(user)
    
    token_payload = TokenPayload(
        user_id=str(user.id),
        username=user.username,
        is_activated=user.is_activated,
        is_staff=user.is_staff,
    )
    
    access_token = await create_access_token(data=token_payload)
    refresh_token = await create_refresh_token(data=token_payload)
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/token/refresh", response_model=Token)
async def refresh_token(
    token_refresh_request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_async_session),
):
    refresh_token = token_refresh_request.refresh_token
    if await is_token_blacklisted(refresh_token, db):
        raise HTTPException(status_code=400, detail="Token is blacklisted")

    try:
        payload = await verify_token(refresh_token, "refresh")

        token_payload = TokenPayload(
            user_id=str(payload.user_id),
            username=payload.username,
            is_activated=payload.is_activated,
            is_staff=payload.is_staff,
        )

        new_access_token = await create_access_token(data=token_payload)

        new_refresh_token = await create_refresh_token(data=token_payload)

        await blacklist_token(refresh_token, db)

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    except Exception as e:
        logging.error(f"Error during token refresh: {e}")  # Log the error for debugging
        raise HTTPException(status_code=403, detail="Token is invalid or expired")


@router.post('/password-forgot')
async def forgot_password(identifier: ForgotPasswordEmailSchema, request: Request, db: AsyncSession = Depends(get_async_session)):
    identifier = identifier.identifier
    try:
        user = await get_object(Users, session=db, username=identifier)
    except Exception:
        user = await get_object(Users, session=db, email=identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or email",
        ) 
    email_sender = ResetPasswordEmailSender()

    await email_sender.send_email(user, request)
    
    return {'detail': 'email was sent'}
    

@router.post("/password-reset")
async def email_verification(token: str, user_request: UserPasswordResetSchema, db: AsyncSession = Depends(get_async_session)):
    token = token.strip()
    if not await is_token_blacklisted(token, db):  # Fix #1: await the function
        try:
            token_data = await verify_token(token, 'access')
            user_id = str(token_data.user_id)

            user = await get_object(Users, session=db, id=user_id)
            if user:
                if not await validate_password(user_request.new_password1):  # No need to try/except if you're going to raise the same exception
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password isn't valid")
                
                if user_request.new_password1 != user_request.new_password2:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Two passwords didn't match")

                user.password = get_password_hash(user_request.new_password1)
                await db.commit()
                await db.refresh(user)

                token_payload = TokenPayload(
                    user_id=str(user.id),
                    username=user.username,
                    is_activated=user.is_activated,
                    is_staff=user.is_staff,
                )

                await blacklist_token(token, db)  # Blacklist the token used for reset
                
                access_token = await create_access_token(data=token_payload)
                refresh_token = await create_refresh_token(data=token_payload)
                
                return {
                    "detail": "Password reset successfully. You can now login with your new password.",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                }
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")  # More accurate error message

        except HTTPException:  # Catch only HTTPExceptions here
            raise
        except Exception as e:  # Catch all other exceptions here
            logging.error(f"An error occurred: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error occurred during password reset")
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired or invalid", headers={"WWW-Authenticate": "Bearer"})  # More accurate error message


@router.post('/delete')
async def delete_account(user: Users = Depends(get_current_user), db: AsyncSession = Depends(get_async_session)):
    try:
        await db.delete(user)
        await db.commit()
        return {"detail": "User deleted successfully."}
    except SQLAlchemyError as e:
            await db.rollback()
            logging.error(f"Error deleting user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not delete user."
            )


@router.post('/logout')
async def logout():
    return {"detail": "You was logout"}