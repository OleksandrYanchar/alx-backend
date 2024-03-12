from typing import List
from fastapi import APIRouter, Depends, HTTPException
from services.posts import  perfome_create_category, perfome_create_subcategory
from crud.categories import crud_category, crud_subcategory
from dependencies.db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.categories import CreateCategorySchema, CategoryInfoSchema, CreateSubCategorySchema, SubCategoryInfoSchema
from dependencies.users import is_user_stuff

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.post("/create/category", dependencies=[Depends(is_user_stuff)], response_model=CategoryInfoSchema)
async def create_category(
    category_data: CreateCategorySchema, 
    db: AsyncSession = Depends(get_async_session),
) -> CategoryInfoSchema:
    """
    Asynchronously create category.
    """
    return await perfome_create_category(category_data, db)


@router.post("/create/subcategory", dependencies=[Depends(is_user_stuff)], response_model=CategoryInfoSchema)
async def create_subcategory(
    subcategory_data: CreateSubCategorySchema, 
    db: AsyncSession = Depends(get_async_session),
) -> SubCategoryInfoSchema:
    """
    Asynchronously create category.
    """
    return await perfome_create_subcategory(subcategory_data, db)

@router.get('/all', response_model=List[CategoryInfoSchema])
async def get_categories(offset: int = 0, limit: int = 999, db: AsyncSession = Depends(get_async_session)):
    """
    Asynchronously displays all category.
    """
    return await crud_category.get_multi(db, offset=offset, limit=limit)


@router.get('/sub/all', response_model=List[SubCategoryInfoSchema])
async def get_categiries(offset: int =0, limit: int = 999, db: AsyncSession=Depends(get_async_session)):
    
    return await crud_subcategory.get_multi(db, offset=offset, limit=limit)


@router.get('/{category_slug}/sub/all', response_model=List[SubCategoryInfoSchema])
async def get_categories(category_slug: str, offset: int = 0, limit: int = 999, db: AsyncSession = Depends(get_async_session)):
    # First, fetch the category by its title to get its ID
    category = await crud_category.get(db, slug=category_slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Then, fetch subcategories that belong to this category
    return await crud_subcategory.get_multi(db,category_id=category.id, offset=offset, limit=limit)

