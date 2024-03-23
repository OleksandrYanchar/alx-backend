import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from schemas.tokens import RefreshTokenRequestSchema, TokenSchema
from schemas.email import ForgotPasswordEmailSchema
from dependencies.auth import get_current_user
from services.tokens import (
    blacklist_token,
    create_jwt_tokens,
    is_token_blacklisted,
    verify_token,
)
from sqlalchemy.exc import SQLAlchemyError
from services.email import reset_email_sender, verify_email_sender
from dependencies.db import get_async_session
from schemas.users import (
    UserCreateInSchema,
    UserCreateOutSchema,
    UserPasswordChangeSchema,
    UserPasswordResetSchema,
)
from services.auth import get_password_hash, verify_password, verify_user_credentials
from services.validators import is_unique, validate_password, validate_email
from models.users import Users
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from crud.users import crud_user


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/signup", response_model=UserCreateOutSchema)
async def create_user(
    user_request: UserCreateInSchema,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> UserCreateOutSchema:
    """
    Asynchronously registrate user.

    Parameters:
    - user_request: UserCreateSchema schema wihch descripes fields and their types required for registartion.
    - db: Async database session.

    Returns:
    - True if all fields are unique, otherwise raises an HTTPException with status code 400 and details of duplicates.
    """
    try:
        if await validate_password(user_request.password) and await validate_email(
            user_request.email
        ):
            if await is_unique(
                db, Users, {"email": user_request.email, "username": user_request.username}
            ):
                
                # Hash password and create user
                user_request.password = get_password_hash(user_request.password)
                obj_in = UserCreateInSchema(**user_request.dict())
                new_user = await crud_user.create(
                    db, obj_in
                )  # This should return the new user object with an ID

                await verify_email_sender.send_email(new_user, request)

                # Generate tokens using the new_user object, which has an 'id'
                tokens = await create_jwt_tokens(
                    new_user
                )  # Pass new_user instead of user_request

                # Prepare the output data
                # Ensure you are returning a structure that includes the new_user data and tokens correctly
                return UserCreateOutSchema(**new_user.dict(), tokens=tokens)  # Adjust
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )


@router.get("/verification")
async def email_verification(token: str, db: AsyncSession = Depends(get_async_session)):
    # Remove any whitespace or newline characters from the token string

    try:
        token = token.strip()
        token_data = await verify_token(
            token, "access_token"
        )  # Assuming verify_token is designed to work as is
        user_id = str(token_data.user_id)  # Adapted based on your TokenPayload schema

        user = await crud_user.get(db, id=user_id)


        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user.is_activated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is already activated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await crud_user.update(
                db, db_obj=user, obj_in={"is_activated": True}
            )

        return {"username": user.username, "is_active": user.is_activated}
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )



@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    try: 
        user = await verify_user_credentials(
            form_data.username, form_data.password, session
        )
        tokens = await create_jwt_tokens(user)  # Await the async function call
        return tokens
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during verifying credentials",
        )

@router.post("/password-change")
async def change_password(
    user_request: UserPasswordChangeSchema,
    db: AsyncSession = Depends(get_async_session),
    user: Users = Depends(get_current_user),
):
    
    try:
        if not verify_password(user_request.old_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect."
            )

        if not await validate_password(user_request.new_password1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="New password isn't valid"
            )

        if user_request.new_password1 != user_request.new_password2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Two passwords didn't match"
            )

        # Hash new password before saving
        new_password = get_password_hash(user_request.new_password1)

        user = await crud_user.update(db, db_obj=user, obj_in={"password": new_password})

        tokens = await create_jwt_tokens(user)  # Await the async function call
        return tokens
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )

@router.post("/token/refresh", response_model=TokenSchema)
async def refresh_token(
    refresh_token_request: RefreshTokenRequestSchema,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        refresh_token = refresh_token_request.token
        if await is_token_blacklisted(refresh_token, db):
            raise HTTPException(status_code=400, detail="Token is blacklisted")

        payload = await verify_token(refresh_token, "refresh_token")

        # Assuming you have a method to retrieve a Users object by id
        user = await crud_user.get(db, id=payload.user_id)

        tokens = await create_jwt_tokens(
            user
        )  # Pass the user object to create new tokens
        await blacklist_token(refresh_token, db)
        return tokens
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )


@router.post("/password-forgot")
async def forgot_password(
    identifier: ForgotPasswordEmailSchema,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        identifier = identifier.identifier
        user = await crud_user.get(db, username=identifier)
        if not user:
            user = await crud_user.get(db, email=identifier)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect username or email",
        )
        await reset_email_sender.send_email(user, request)

        return {"detail": "email was sent"}
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )


@router.post("/password-reset")
async def rest_email_verification(
    token: str,
    user_request: UserPasswordResetSchema,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        token = token.strip()

        if  await is_token_blacklisted(token, db): 
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is expired or invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )  

        token_data = await verify_token(token, "access")
        user_id = str(token_data.user_id)

        user = await crud_user.get(db, id=user_id)

        if user:

            if not await validate_password(
                user_request.new_password1
            ):  
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password isn't valid",
                )

            if user_request.new_password1 != user_request.new_password2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Two passwords didn't match",
                )

            new_password = get_password_hash(user_request.new_password1)

            user = await crud_user.update(
                db, db_obj=user, obj_in={"password": new_password}
            )

            await blacklist_token(token, db)  

            token_schema = await create_jwt_tokens(
                user
            )  
            return token_schema

        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )  

    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )


@router.delete("/delete")
async def delete_account(
    user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        await crud_user.delete(db, db_obj=user)
        return {"detail": "User deleted successfully."}
    except SQLAlchemyError as e:
        logging.error(f"Verification error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete user.",
        )
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )

@router.post("/logout")
async def logout():
    return {"detail": "You was logout"}
