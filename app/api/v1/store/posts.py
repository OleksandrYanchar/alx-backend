from datetime import date, datetime
import logging
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, status, UploadFile
from utils.posts import (
    check_user_posts_limits,
    prepare_post_data_for_response,
    validate_and_transform_category_subcategory,
    validate_owner,
    validate_post_create_data,
)
from configs.general import (
    POSTS_PICTURES_DIR,
    VIPS_POST_IMAGES_LIMIT,
    POST_IMAGES_LIMIT,
)
from tasks.store import upload_picture
from dependencies.store import is_user_owner_or_stuff
from schemas.pagination import PaginationSchema
from dependencies.auth import get_current_user
from crud.categories import crud_subcategory, crud_category
from schemas.users import UserDataSchema
from crud.posts import crud_postimage, crud_post
from dependencies.db import get_async_session
from models.users import Users
from schemas.posts import (
    PostCreateInSchema,
    PostImageUpdate,
    PostUpdateSchema,
)
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.posts import PostInfoSchema
from dependencies.users import is_user_activated
from fastapi_cache.decorator import cache
from starlette.requests import Request
from starlette.responses import Response

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)


@router.post(
    "/create", dependencies=[Depends(is_user_activated)], response_model=PostInfoSchema
)
async def create_post_handler(
    post_data: PostCreateInSchema,
    owner: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> PostInfoSchema:
    # Check user post limits
    await check_user_posts_limits(db, owner)

    # Validate and transform category and subcategory
    try:
        # Fetch category and subcategory objects based on provided strings
        category = await crud_category.get(db, title=post_data.category)
        subcategory = await crud_subcategory.get(db, title=post_data.subcategory)

        # Validate post creation data
        await validate_post_create_data(post_data, category, subcategory)

        # Prepare the post creation dictionary
        post_create_dict = post_data.dict(
            exclude={"category", "subcategory"},
        )
        post_create_dict.update(
            {
                "owner": owner.id,
                "category_id": category.id,
                "sub_category_id": subcategory.id,
            }
        )

        # Create the post
        created_post = await crud_post.create(db, obj_in=post_create_dict)

        # Prepare post info for the response
        post_info = await prepare_post_data_for_response(db, created_post)

        # Add additional fields to post_info if needed
        post_info["owner"] = UserDataSchema.from_orm(owner)
        post_info["category"] = category.title
        post_info["subcategory"] = subcategory.title

        # Fetch and add images for the post
        post_images = await crud_postimage.get_multi(db, post=created_post.id)
        images_info = [image.image for image in post_images]
        post_info["images"] = images_info

        return PostInfoSchema(**post_info)

    except HTTPException as e:
        raise e

    except Exception as e:
        logging.error(f"Creating post error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during post creation",
        )


@cache(expire=60)
@router.get("/all", response_model=PaginationSchema[PostInfoSchema])
async def get_posts(
    offset: int = Query(default=0),
    limit: int = Query(default=2),
    order_by: str = None,
    id: str = None,
    title: str = None,
    category_title: str = None,
    subcategory_title: str = None,
    owner_username: str = None,
    created_start_date: Optional[date] = None,
    created_end_date: Optional[date] = None,
    is_vip: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    detail: str = "ok",
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_async_session),
) -> PaginationSchema[PostInfoSchema]:
    try:
        category, subcategory = None, None
        if category_title and subcategory_title:
            category, subcategory = await validate_and_transform_category_subcategory(
                db, category_title, subcategory_title
            )

        owner_id = None
        if owner_username:
            owner = await validate_owner(db, username=owner_username)
            owner_id = owner.id

        posts, total = await crud_post.get_multi_filtered(
            db,
            offset=offset,
            limit=limit,
            is_vip=is_vip,
            min_price=min_price,
            max_price=max_price,
            id=id,
            title=title,
            category=category.id if category else None,
            subcategory=subcategory.id if subcategory else None,
            owner=owner_id,
            created_start_date=created_start_date,
            created_end_date=created_end_date,
            order_by=order_by,
        )

        result_posts = [
            await prepare_post_data_for_response(db, post) for post in posts
        ]

        return PaginationSchema[PostInfoSchema](
            total=total, items=result_posts, offset=offset, limit=limit, detail=detail
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"getting all posts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during getting posts",
        )


@cache(expire=60)
@router.get("/id/{id}", response_model=PostInfoSchema)
async def get_post(
    id: str,
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_async_session),
) -> PostInfoSchema:
    try:
        post = await crud_post.get(db, id=id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        post_data = await prepare_post_data_for_response(db, post, include_images=True)

        return PostInfoSchema(**post_data)

    except HTTPException as e:
        raise e

    except Exception as e:
        logging.error(f"getting post by id error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during getting post",
        )


@cache(expire=60)
@router.get("/user/{username}/all", response_model=PaginationSchema[PostInfoSchema])
async def get_posts_by_username(
    username: str,
    offset: int = Query(default=0),
    limit: int = Query(default=2),
    order_by: str = None,
    id: str = None,
    category_title: str = None,
    subcategory_title: str = None,
    created_start_date: Optional[date] = None,
    created_end_date: Optional[date] = None,
    is_vip: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    detail: str = "ok",
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_async_session),
) -> PaginationSchema[PostInfoSchema]:

    try:
        owner = await validate_owner(db, username=username)

        category, subcategory = None, None
        if category_title and subcategory_title:
            category, subcategory = await validate_and_transform_category_subcategory(
                db, category_title, subcategory_title
            )

        posts, total = await crud_post.get_multi_filtered(
            db,
            offset=offset,
            limit=limit,
            is_vip=is_vip,
            min_price=min_price,
            max_price=max_price,
            id=id,
            category=category.id if category else None,
            subcategory=subcategory.id if subcategory else None,
            owner=owner.id,
            created_start_date=created_start_date,
            created_end_date=created_end_date,
            order_by=order_by,
        )
        result_posts = [
            await prepare_post_data_for_response(db, post) for post in posts
        ]

        return PaginationSchema[PostInfoSchema](
            total=total, items=result_posts, offset=offset, limit=limit, detail=detail
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"getting user's posts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during getting user's posts",
        )


@router.put("/update/{post_id}", response_model=PostInfoSchema)
async def update_post_info(
    post_id: str,
    post_data: PostUpdateSchema,
    user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):

    try:
        # Fetch the post to update
        post = await crud_post.get(db, id=post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Check if the current user is the owner of the post
        if user.id != post.owner:
            raise HTTPException(
                status_code=403, detail="You don't have enough permissions"
            )

        # Validate and transform category and subcategory
        category, subcategory = await validate_and_transform_category_subcategory(
            db,
            category_title=post_data.category
            if post_data.category
            else post.category_id,
            subcategory_title=post_data.subcategory
            if post_data.subcategory
            else post.sub_category_id,
        )

        # Prepare update data
        update_data = post_data.dict(exclude_unset=True)
        update_data.pop("created_at", None)  # Exclude creation time from updates
        update_data["updated_at"] = datetime.now()  # Update the 'updated_at' field
        update_data["category_id"] = category.id
        update_data["sub_category_id"] = subcategory.id

        # Perform the update operation
        updated_post = await crud_post.update(db, db_obj=post, obj_in=update_data)

        # Prepare and return the updated post data
        post_info = await prepare_post_data_for_response(
            db, updated_post, include_images=True
        )
        return PostInfoSchema(**post_info)

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Updating post error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during updating post",
        )


@router.post("/{post_id}/upload-photo", dependencies=[Depends(is_user_owner_or_stuff)])
async def upload_post_photo(
    post_id: str,
    user: Users = Depends(get_current_user),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_async_session),
):

    upload_limit = VIPS_POST_IMAGES_LIMIT if user.is_vip else POST_IMAGES_LIMIT
    if len(files) > upload_limit:
        raise HTTPException(
            detail=f"Image limit exceeded, upload up to {upload_limit} images",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:

        # Check if the number of files exceeds the limit
        existing_images = await crud_postimage.get_multi(db=db, post=post_id)

        # If there are existing images, delete them from the database and the folder
        if existing_images:
            for image in existing_images:
                # Delete the file from the filesystem
                actual_file_name = image.image.split("/")[-1]
                file_path = os.path.join(POSTS_PICTURES_DIR, actual_file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                # Delete the record from the database
                await crud_postimage.delete(db=db, id=image.id)

        # Process each file
        for file in files:
            # Read the file content
            file_content = await file.read()
            filename = file.filename

            # Asynchronously upload the picture and wait for the result
            task_result = upload_picture.delay(
                file_content, filename, POSTS_PICTURES_DIR
            )
            file_url = task_result.get(timeout=10)

            # Create new PostImage object with 'images' as a list of URLs
            post_image_in = PostImageUpdate(
                post=post_id, image=file_url
            )  # Corrected here
            new_post_image = await crud_postimage.create(db, obj_in=post_image_in)

            # Confirm new_post_image is not None and is persisted successfully
            if not new_post_image:
                raise HTTPException(
                    detail="Failed to save image information to the database",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        await db.commit()  # Make sure to commit after all changes

        return {"detail": "images were saved"}

    except Exception as e:
        await db.rollback()  # Rollback in case of any exception
        logging.error(f"File upload error: {e}", exc_info=True)
        raise HTTPException(
            detail="Internal server error occurred during uploading image",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/delete/{post_id}", dependencies=[Depends(is_user_owner_or_stuff)])
async def upload_post_photo(
    post_id: str,
    user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):

    try:
        post = await crud_post.get(id=post_id)
        # Check if the number of files exceeds the limit
        await crud_post.delete(db, db_obj=post)
        return {"detail": "Post deleted successfully."}

    except Exception as e:
        await db.rollback()  # Rollback in case of any exception
        logging.error(f"File upload error: {e}", exc_info=True)
        raise HTTPException(
            detail="Internal server error occurred during uploading image",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
