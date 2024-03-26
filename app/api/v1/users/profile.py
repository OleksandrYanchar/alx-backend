
import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from configs.general import AVATARS_DIR
from tasks.store import upload_picture
from schemas.users import UserDataSchema
from models.users import Users
from dependencies.db import get_async_session
from dependencies.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
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


@router.put('/update-image')
async def update_photo(file: UploadFile = File(...), user: Users = Depends(get_current_user), db: AsyncSession = Depends(get_async_session)):
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    file_content = await file.read()
    filename = file.filename

    # Call the task with file content and filename
    task_result = upload_picture.delay(file_content, filename, AVATARS_DIR)
    file_url = task_result.get(timeout=10)  

    try:
        updated_user = await crud_user.update(db, db_obj=user, obj_in={"image": file_url})
        return {"detail": "Image uploaded successfully.", 'image': file_url}
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )