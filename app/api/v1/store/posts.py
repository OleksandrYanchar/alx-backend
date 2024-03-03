from fastapi import APIRouter, Depends
from crud.posts import crud_post
from crud.categories import crud_category 
from dependencies.db import get_async_session
from models.users import Users
from schemas.posts import PostCreateInSchema
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.posts import PostCreateOutSchema
from dependencies.users import is_user_activated


router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)


@router.post("/create", response_model=PostCreateOutSchema)
async def create_post(
    post_data: PostCreateInSchema,
    owner: Users= Depends(is_user_activated), 
    db: AsyncSession = Depends(get_async_session),
) -> PostCreateOutSchema:
    """
    Asynchronously create post.

    Parameters:
    - post_data: PostCreateInSchema schema wihch descripes fields and their types required for creating.
    - db: Async database session.
    - user: Currently loggined user  
    
    Returns:
    - True PostCreateOutSchema data if fields are unique, otherwise raises an HTTPException with status code 400 and details.
    """
    post_data = post_data.dict
    post_data['owner']= owner
    post_data['category']= crud_category.get()
    new_post = await crud_post.create(
                db, obj_in=post_data  # Pass the modified dictionary with the owner field
            ) 
    return PostCreateOutSchema(**new_post.dict())
