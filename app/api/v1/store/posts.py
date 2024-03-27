from datetime import date, datetime
import logging
import os
from typing import  List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, status, UploadFile
from configs.general import POSTS_PICTURES_DIR, VIPS_POST_IMAGES_LIMIT, POST_IMAGES_LIMIT, POSTS_LIMIT, VIPS_POSTS_LIMIT
from tasks.store import upload_picture
from dependencies.store import is_user_owner_or_stuff
from schemas.pagination import PaginationSchema
from crud.users import crud_user
from dependencies.auth import get_current_user
from crud.categories import crud_subcategory, crud_category
from schemas.users import UserDataSchema
from services.posts import clean_title
from crud.posts import crud_postimage, crud_post 
from dependencies.db import get_async_session
from models.users import Users
from schemas.posts import PostCreateInSchema, PostImageUpdate, PostUpdateSchema, PostImageInfo
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


@router.post("/create", dependencies=[Depends(is_user_activated)], response_model=PostInfoSchema)
async def create_post_handler(
    post_data: PostCreateInSchema,
    owner: Users= Depends(get_current_user),  # Assuming this correctly extracts the user and its UUID
    db: AsyncSession = Depends(get_async_session),
) -> PostInfoSchema:
    
    posts, total_post_count = await crud_post.get_multi_filtered(db=db, owner=owner.id)  # No need to fetch posts, just the count
    upload_limit = VIPS_POST_IMAGES_LIMIT if owner.is_vip else POST_IMAGES_LIMIT
    
    if total_post_count >= upload_limit:
        raise HTTPException(
            detail=f"Post limit exceeded, you can create up to {upload_limit} posts",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        if post_data.price < 0 :
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="price can't be negative",
            )

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

        post_images = await crud_postimage.get_multi(db, post=created_post.id)
        images_info = [PostImageInfo(image=image.image) for image in post_images]
        
        # Remove the 'owner' key manually
        if 'owner' in post_info:
            del post_info['owner']

        # Then proceed with your return statement
        return PostInfoSchema(**post_info, owner=UserDataSchema(**owner.dict()), category=category.title, subcategory=subcategory.title, images=images_info)

    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"creating post error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during creating",
        )
 
@cache(expire=60)
@router.get("/all", response_model=PaginationSchema[PostInfoSchema])
async def get_posts( 
    offset: int = Query(default=0),  
    limit: int = Query(default=2), 
    order_by: str = None,
    id: str = None,
    title: str = None,
    category: str = None,
    subcategory: str = None,
    owner: str = None,
    created_start_date: Optional[date] = None,
    created_end_date: Optional[date] = None,
    is_vip: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    detail: str = 'ok',
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_async_session)
) -> PaginationSchema[PostInfoSchema]:
     
    try:
        if category:
            category_obj = await crud_category.get(db, title=category)
            if not category_obj:
                detail = "Category not found"
            else:
                category = category_obj.id

        if subcategory:
            subcategory_obj = await crud_subcategory.get(db, title=subcategory)
            if not subcategory_obj:
                detail = "Subcategory not found"
            else:
                subcategory = subcategory_obj.id

        owner_id = None  # Initialize owner_id as None
        if owner:
            owner_obj = await crud_user.get(db, username=owner)
            if not owner_obj:
                detail = "Owner not found"
            else:
                owner_id = owner_obj.id  # Use

        posts, total = await crud_post.get_multi_filtered(
            db, 
            offset=offset, 
            limit=limit,
            is_vip=is_vip,
            min_price=min_price,
            max_price=max_price,
            id=id,
            title=title,
            category=category,
            subcategory=subcategory,
            owner=owner_id,
            created_start_date=created_start_date,
            created_end_date=created_end_date,
            order_by=order_by,
            created_at_field_name = 'created_at',  
            vip_field_name = 'is_vip', 
            price_field_name = 'price',
            title_field_name='title',
            category_field_name='category_id',
            subcategory_field_name='sub_category_id',
            owner_field_name='owner',
        )
        
        result_posts = []
        
        if not posts:
            
            return PaginationSchema[PostInfoSchema](total=0, items=result_posts, offset=offset, limit=limit, detail='no posts') 


        for post in posts:
            category = await crud_category.get(db, id=post.category_id)
            subcategory = await crud_subcategory.get(db, id=post.sub_category_id)
            
            owner =  await crud_user.get(db, id=post.owner)

            post_data = post.dict()
            
            if 'owner' in post_data:
                del post_data['owner']
            
            post_data.update({
                'category': category.title if category else "Category not found",
                'subcategory': subcategory.title if subcategory else "Subcategory not found",
                'owner': UserDataSchema(**owner.dict())
            })

            # Fetch and add images for each post
            post_images = await crud_postimage.get_multi(db, post=post.id)
            images_info = [PostImageInfo(image=image.image) for image in post_images]
            post_data['images'] = images_info  # Add images to post data

            # Append the constructed PostInfoSchema to result_posts
            result_posts.append(PostInfoSchema(**post_data))

        # Properly return an instance of PaginationSchema with the list of post_info objects
        return PaginationSchema[PostInfoSchema](
            total=total, 
            items=result_posts, 
            offset=offset, 
            limit=limit, 
            detail=detail
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
async def get_post(id: str, request: Request = None, response: Response = None, db: AsyncSession=Depends(get_async_session)) -> PostInfoSchema:
    
    try:
        post = await crud_post.get(db, id=id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Assuming `crud_post.get` fetches the post with relational fields loaded,
        # or you have separate methods to fetch category and subcategory details.
        owner = await crud_user.get(db, id=post.owner)
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")

        # Fetch category and subcategory information if not already included in `post`
        category = await crud_category.get(db, id=post.category_id)
        subcategory = await crud_subcategory.get(db, id=post.sub_category_id)

        if not category or not subcategory:
            raise HTTPException(status_code=404, detail="Category or Subcategory not found")

        post_data = post.dict()
        
        if 'owner' in post_data:
            del post_data['owner']

        # Add category and subcategory titles to post_data
        post_data.update({
                'category': category.title if category else "Category not found",
                'subcategory': subcategory.title if subcategory else "Subcategory not found",
                'owner': UserDataSchema(**owner.dict())
            })

            # Fetch and add images for each post
        post_images = await crud_postimage.get_multi(db, post=post.id)
        images_info = [PostImageInfo(image=image.image) for image in post_images]
        post_data['images'] = images_info  # Add images to post data

        
        # Then proceed with your return statement
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
async def get_posts_by_username(username: str, 
    offset: int = Query(default=0),  
    limit: int = Query(default=2), 
    order_by: str = None,
    id: str = None,
    category: str = None,
    subcategory: str = None,
    owner: str = None,
    created_start_date: Optional[date] = None,
    created_end_date: Optional[date] = None,
    is_vip: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    detail: str = 'ok',
    request: Request = None,
    response: Response = None,
    db: AsyncSession = Depends(get_async_session)
) -> PaginationSchema[PostInfoSchema]:
    
    try:
        owner = await crud_user.get(db, username=username)
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")

        posts, total = await crud_post.get_multi_filtered(
            db, 
            offset=offset, 
            limit=limit,
            is_vip=is_vip,
            min_price=min_price,
            max_price=max_price,
            id=id,
            category=category,
            subcategory=subcategory,
            owner=owner.id,
            created_start_date=created_start_date,
            created_end_date=created_end_date,
            order_by=order_by,
            created_at_field_name = 'created_at',  
            vip_field_name = 'is_vip', 
            price_field_name = 'price',
            category_field_name='category_id',
            subcategory_field_name='sub_category_id',
            owner_field_name='owner',
        )
        result_posts = []

        for post in posts:
            category = await crud_category.get(db, id=post.category_id)
            subcategory = await crud_subcategory.get(db, id=post.sub_category_id)
            post_images = await crud_postimage.get_multi(db, post=post.id)

            post_data = post.dict()

            post_data.update({
                'category': category.title if category else "Category not found",
                'subcategory': subcategory.title if subcategory else "Subcategory not found",
                'owner': UserDataSchema(**owner.dict())
            })

            # Fetch and add images for each post
            post_images = await crud_postimage.get_multi(db, post=post.id)
            images_info = [PostImageInfo(image=image.image) for image in post_images]
            post_data['images'] = images_info  # Add images to post data

            # Append the constructed PostInfoSchema to result_posts
            result_posts.append(PostInfoSchema(**post_data))

        # Properly return an instance of PaginationSchema with the list of post_info objects
        return PaginationSchema[PostInfoSchema](
            total=total, 
            items=result_posts, 
            offset=offset, 
            limit=limit, 
            detail=detail
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
async def update_post_info(post_id: str, post_data: PostUpdateSchema, user: Users = Depends(get_current_user), db: AsyncSession = Depends(get_async_session)):
   
    try:
        post = await crud_post.get(db, id=post_id)

        if user.id != post.owner:
            raise HTTPException(status_code=404, detail="You don't have enough permissions")

        if not post_data.category:
            category = await crud_category.get(db, id=post.category_id)
        else:
            category = await crud_category.get(db, title=await clean_title(post_data.category))

        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")

        if not post_data.subcategory:
            subcategory = await crud_subcategory.get(db, id=post.sub_category_id)
        else:
            subcategory = await crud_subcategory.get(db, title=await clean_title(post_data.subcategory))

        if subcategory is None:
            raise HTTPException(status_code=404, detail="Subcategory not found")


        update_data = post_data.dict(exclude_unset=True)

        update_data.pop('created_at', None)  
        update_data['updated_at'] = datetime.now()
        created_post = await crud_post.update(db, obj_in=update_data)    

        if created_post is None or user is None:
            return {"error": "Post creation or owner retrieval failed"}

        post_info = created_post.dict()

        if 'owner' in post_info:
            del post_info['owner']

        return PostInfoSchema(**post_info, owner=UserDataSchema(**user.dict()), category=category.title, subcategory=subcategory.title)
    
    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"updating post error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during updating post",
        )



@router.post('/{post_id}/upload-photo', dependencies=[Depends(is_user_owner_or_stuff)])
async def upload_post_photo(post_id: str,
                            user: Users = Depends(get_current_user),
                            files: List[UploadFile] = File(...), 
                            db: AsyncSession = Depends(get_async_session)):

    upload_limit = VIPS_POST_IMAGES_LIMIT if user.is_vip else POST_IMAGES_LIMIT
    if len(files) > upload_limit:
        raise HTTPException(
            detail=f"Image limit exceeded, upload up to {upload_limit} images",
            status_code=status.HTTP_400_BAD_REQUEST
        )   
            
    try:
        
        # Check if the number of files exceeds the limit
        existing_images = await crud_postimage.get_multi(
            db=db, post=post_id
        )
        
        # If there are existing images, delete them from the database and the folder
        if existing_images:
            for image in existing_images:
                # Delete the file from the filesystem
                actual_file_name = image.image.split('/')[-1]
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
            task_result = upload_picture.delay(file_content, filename, POSTS_PICTURES_DIR)
            file_url = task_result.get(timeout=10)

            # Create new PostImage object with 'images' as a list of URLs
            post_image_in = PostImageUpdate(post=post_id, image=file_url)  # Corrected here
            new_post_image = await crud_postimage.create(db, obj_in=post_image_in)
                    
            # Confirm new_post_image is not None and is persisted successfully
            if not new_post_image:
                raise HTTPException(
                    detail="Failed to save image information to the database",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        await db.commit()  # Make sure to commit after all changes
        
        return {'detail': 'images were saved'}
        
        
    except Exception as e:
        await db.rollback()  # Rollback in case of any exception
        logging.error(f'File upload error: {e}', exc_info=True)
        raise HTTPException(
            detail="Internal server error occurred during uploading image",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )