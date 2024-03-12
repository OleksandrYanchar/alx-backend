
import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import secrets
from schemas.users import UserDataSchema
from models.users import Users
from dependencies.db import get_async_session
from dependencies.auth import get_current_user
from configs.general import  MEDIA_FILES_PATH
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
from crud.users import crud_user
import uuid

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
)

@router.get('/{user_id}', response_model=UserDataSchema)
async def get_user_info(user_id: uuid.UUID, db: AsyncSession = Depends(get_async_session) ):
    
    user = await crud_user.get(db, id=user_id)
    
    if user is None:
    
            raise HTTPException(
                status_code=404,
                detail="The user with this username does not exist in the system",
            )
        
    return user


@router.post('/update-image/')
async def update_photo(file: UploadFile = File(...), user: Users = Depends(get_current_user), db: AsyncSession = Depends(get_async_session)):

    """
    Update the image for a specific user.
    """
    try:
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        filename = file.filename
        extension = filename.split(".")[-1].lower()
        if extension not in ["jpg", "png"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File extension must be .jpg or .png")

        # Here you would save the file in a directory or cloud storage
        # For simplicity, let's assume you're saving the file locally
        token_name = secrets.token_hex(10) + "." + extension
        generated_name = MEDIA_FILES_PATH + f'avatars/{token_name}'
        file_url = generated_name.split('static/')[1]

        # Write the file asynchronously
        try:
            file_content = await file.read()
            async with aiofiles.open(generated_name, "wb") as out_file:
                await out_file.write(file_content)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        # Process the image
        try:
            with Image.open(generated_name) as img:
                img = img.resize(size=(512, 512))
                img.save(generated_name)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unable to process image")

        # Update the user record
        try:
            user = await crud_user.update(db, db_obj=user, obj_in={"image": file_url})
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save user info")

        return { 
                "detail": "Image uploaded successfully.",
                'image': file_url}
                
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )