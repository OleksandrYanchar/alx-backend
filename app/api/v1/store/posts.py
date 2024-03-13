from datetime import date, datetime
import logging
from typing import  Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from schemas.pagination import PaginationSchema
from crud.users import crud_user
from dependencies.auth import get_current_user
from crud.categories import crud_subcategory, crud_category
from schemas.users import UserDataSchema
from services.posts import clean_title
from crud.posts import crud_post 
from dependencies.db import get_async_session
from models.users import Users
from schemas.posts import PostCreateInSchema, PostUpdateSchema
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

        # Remove the 'owner' key manually
        if 'owner' in post_info:
            del post_info['owner']

        # Then proceed with your return statement
        return PostInfoSchema(**post_info, owner=UserDataSchema(**owner.dict()), category=category.title, subcategory=subcategory.title)

    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )
 
 
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
            
            post_data['category'] = category.title if category else "Category not found"
            post_data['subcategory'] = subcategory.title if subcategory else "Subcategory not found"
            
            owner_data = UserDataSchema(**owner.dict())
            post_info = PostInfoSchema(**post_data, owner=owner_data)
            
            result_posts.append(post_info)


        return PaginationSchema[PostInfoSchema](total=total, items=result_posts, offset=offset, limit=limit, detail=detail) 

    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )


@router.get("/id/{id}", response_model=PostInfoSchema)
async def get_post(id: str, db: AsyncSession=Depends(get_async_session)) -> PostInfoSchema:
    
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
        post_data['category'] = category.title if category else None
        post_data['subcategory'] = subcategory.title if subcategory else None

        return PostInfoSchema(**post_data, owner=UserDataSchema(**owner.dict()))

    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )


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
            
            post_data = post.dict()
            if 'owner' in post_data:
                del post_data['owner']
            
            post_data['category'] = category.title if category else "Category not found"
            post_data['subcategory'] = subcategory.title if subcategory else "Subcategory not found"
            
            owner_data = UserDataSchema(**owner.dict())
            post_info = PostInfoSchema(**post_data, owner=owner_data)
                    
            result_posts.append(post_info) 
            
        return PaginationSchema[PostInfoSchema](total=total, items=result_posts,detail=detail, offset=offset, limit=limit)

    except HTTPException as e:
        raise e
    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
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
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )