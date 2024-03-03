from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from models.posts import Post
from services.pagination import get_total_count
from schemas.pagination import PaginationSchema
from crud.users import crud_user
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


@router.get("/id/{id}", response_model=PostInfoSchema)
async def get_post(id: str, db: AsyncSession=Depends(get_async_session)) -> PostInfoSchema:
    
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


@router.get("/user/{username}/all", response_model=PaginationSchema[PostInfoSchema])
async def get_posts_by_username(username: str, offset: int = 0  , limit: int = 2, db: AsyncSession=Depends(get_async_session)):
    owner = await crud_user.get(db, username=username)
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    posts = await crud_post.get_multi(db, owner=owner.id, offset=offset, limit=limit)
    total = await get_total_count(db, Post, Post.owner == owner.id)
    
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

    return PaginationSchema[PostInfoSchema](total=total, items=result_posts, offset=offset, limit=limit)

@router.get("/category/{slug}", response_model=PaginationSchema[PostInfoSchema])
async def get_posts_by_username(slug: str, offset: int = 0  , limit: int = 2, db: AsyncSession=Depends(get_async_session)):
     
    category_obj = await crud_category.get(db, slug=slug)
    
    posts = await crud_post.get_multi(db, category_id=category_obj.id, offset=offset, limit=limit)
    total = await get_total_count(db, Post, Post.category_id == category_obj.id)
    
    result_posts = []
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

    return PaginationSchema[PostInfoSchema](total=total, items=result_posts, offset=offset, limit=limit)    


@router.get("/{category_slug}/{subcategory_slug}", response_model=PaginationSchema[PostInfoSchema])
async def get_posts_by_username(subcategory_slug: str, category_slug: str, offset: int = 0  , limit: int = 2, db: AsyncSession=Depends(get_async_session)):
     
    subcategory_obj = await crud_subcategory.get(db, slug=subcategory_slug)
    
    category_obj = await crud_category.get(db, slug=category_slug)

    if subcategory_obj.category_id != category_obj.id:
        raise HTTPException(status_code=404, detail="Category or Subcategory not found")
    
    posts = await crud_post.get_multi(db, sub_category_id=subcategory_obj.id, offset=offset, limit=limit)
    total = await get_total_count(db, Post, Post.sub_category_id == subcategory_obj.id)
    
    result_posts = []
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

    return PaginationSchema[PostInfoSchema](total=total, items=result_posts, offset=offset, limit=limit)    