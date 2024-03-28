from fastapi import HTTPException, status

from schemas.posts import PostImageInfo
from schemas.users import UserDataSchema
from crud.users import crud_user
from crud.categories import crud_subcategory, crud_category
from configs.general import POSTS_LIMIT, VIPS_POSTS_LIMIT
from crud.posts import crud_postimage, crud_post, crud_postimage


async def validate_post_create_data(post_data, category, subcategory) -> bool:
    if post_data.price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="price can't be negative",
            )

    # Assuming you fetch the category object before this call
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category does not exist.",
        )

    # Adjust the call to include the 'category' argument
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
    return True

async def check_user_posts_limits(db, owner):
    _ , total_post_count = await crud_post.get_multi_filtered(
    db =db, owner=owner.id
    )  # No need to fetch posts, just the count
    upload_limit = VIPS_POSTS_LIMIT if owner.is_vip else POSTS_LIMIT

    if total_post_count >= upload_limit:
        raise HTTPException(
            detail=f"Post limit exceeded, you can create up to {upload_limit} posts",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        
async def validate_and_transform_category_subcategory(db, category_title, subcategory_title):
    category = await crud_category.get(db, title=category_title)
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")

    subcategory = await crud_subcategory.get(db, title=subcategory_title)
    if not subcategory or subcategory.category_id != category.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subcategory not found or does not belong to the specified category")

    return category, subcategory

async def validate_owner(db, username=None, user_id=None):
    if username:
        owner = await crud_user.get(db, username=username)
    elif user_id:
        owner = await crud_user.get(db, id=user_id)
    else:
        raise ValueError("Either username or user_id must be provided")
    
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")
    
    return owner


async def prepare_post_data_for_response(db, post, include_images=True):
    category = await crud_category.get(db, id=post.category_id)
    subcategory = await crud_subcategory.get(db, id=post.sub_category_id)
    owner = await crud_user.get(db, id=post.owner)

    post_data = post.dict()
    post_data.update({
        "category": category.title if category else "Category not found",
        "subcategory": subcategory.title if subcategory else "Subcategory not found",
        "owner": UserDataSchema(**owner.dict()) if owner else None,
    })

    if include_images:
        post_images = await crud_postimage.get_multi(db, post=post.id)
        images_info = [PostImageInfo(image=image.image) for image in post_images]
        post_data["images"] = images_info

    return post_data
