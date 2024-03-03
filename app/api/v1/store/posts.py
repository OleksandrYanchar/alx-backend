from fastapi import APIRouter, Depends, HTTPException, status
from dependencies.auth import get_current_user
from crud.categories import crud_subcategory, crud_category
from schemas.users import UserDataSchema
from services.posts import clean_title
from crud.posts import crud_post 
from dependencies.db import get_async_session
from models.users import Users
from schemas.posts import PostCreateInSchema
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.posts import PostInfoSchema
from dependencies.users import is_user_activated


router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)


@router.post("/create", dependencies=[Depends(is_user_activated)], response_model=PostInfoSchema)
async def create_post_handler(
    post_data: PostCreateInSchema,
    owner: Users= Depends(get_current_user),  # Assuming this correctly extracts the user and its UUID
    db: AsyncSession = Depends(get_async_session),
) -> PostInfoSchema:

    # Assuming you fetch the category object before this call
    category = await crud_category.get(db, title= await clean_title(post_data.category))
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category does not exist.",
        )
    
    # Adjust the call to include the 'category' argument
    subcategory = await crud_subcategory.get(db, title=post_data.subcategory)
    if not subcategory:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subcategory does not exist or does not belong to the specified category.",
        )

    
    if subcategory.category_id != category.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subcategory is not in the specified category.",
        )

    post_create_dict = post_data.dict(exclude_unset=True)
    post_create_dict.update({"owner": owner.id, "category_id": category.id, "sub_category_id": subcategory.id})

    post_create_dict.pop('category', None)  # Remove 'category' key if it exists
    post_create_dict.pop('subcategory', None)  # Remove 'subcategory' key if it exists
    created_post = await crud_post.create(db, obj_in=post_create_dict)    
    # Retrieve the owner object based on owner_id

    if created_post is None or owner is None:
        # Handle the error if either the post wasn't created or the owner wasn't found
        return {"error": "Post creation or owner retrieval failed"}

    # Since `created_post.dict()` might include an 'owner' key, explicitly exclude it to avoid the TypeError
    post_info = created_post.dict()

    # Remove the 'owner' key manually
    if 'owner' in post_info:
        del post_info['owner']

    # Then proceed with your return statement
    return PostInfoSchema(**post_info, owner=UserDataSchema(**owner.dict()), category=category.title, subcategory=subcategory.title)
