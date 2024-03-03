import re
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from crud.categories import crud_category, crud_subcategory
from schemas.categories import CreateCategorySchema, CategoryInfoSchema, CreateSubCategorySchema, SubCategoryCrateInfoSchema


async def clean_title(title: str) -> str:
    title = title.strip().lower()
    title = re.sub(r'[^a-zA-Z\s]', '', title)
    return re.sub("\ +", " ", title)  


async def create_slug(title: str) -> str:
    # Ensure to call .lower() to convert the title to lowercase
    return title.strip().replace(' ', '-').lower()

async def is_subcategory_in_category(db: AsyncSession, category_id: int, sub_category_id: int):
    return await crud_subcategory.get(db, id=sub_category_id, category_id=category_id)


async def perfome_create_category(
    category_data: CreateCategorySchema, 
    db: AsyncSession,
) -> CategoryInfoSchema:
    title = await clean_title(category_data.title)
    slug = await create_slug(title)
    
    if len(title) >64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A category name is too long, max:64, yours is:{len(title)}",
        )

    if len(slug) >128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A category slug is too long, max:128, yours is:{len(slug)}"
        )

    if await crud_category.get(db, title=title):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this title already exists.",
        )
    if await crud_category.get(db, slug=slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this slug already exists.",
        )
    # Prepare the data for category creation
    category_data = category_data.dict()
    category_data['title'] = title
    category_data['slug'] = slug
    
    # Create the new category and ensure it's returned as a model instance or dict
    new_category = await crud_category.create(db, obj_in=category_data)
    
    # Assuming new_category is an ORM model instance
    return CategoryInfoSchema(**new_category.dict())


async def perfome_create_subcategory(
    subcategory_data: CreateSubCategorySchema, 
    db: AsyncSession,
) -> SubCategoryCrateInfoSchema:
    title = await clean_title(subcategory_data.title)
    slug = await create_slug(title)
    
    if len(title) >64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"title is too long, max:64, yours is:{len(title)}",
        )

    if len(slug) >128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"slug is too long, max:128, yours is:{len(slug)}"
        )
        
    if await crud_subcategory.get(db, title=title):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this title already exists.",
        )
    if await crud_subcategory.get(db, slug=slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="this slug already exists.",
        )
    
    
    category = await crud_category.get(db, title= await clean_title(subcategory_data.category))

    # Prepare the data for subcategory creation
    subcategory_data_dict = subcategory_data.dict(exclude={'category'})
    subcategory_data_dict['title'] = title
    subcategory_data_dict['category_id'] = category.id  # use the retrieved category's ID
    subcategory_data_dict['slug'] = slug

    # Create the new SubCategory using the 'subcategory_data_dict'
    new_subcategory = await crud_subcategory.create(db, obj_in=subcategory_data_dict)

    # Construct the SubCategoryInfoSchema object with the category name included
    subcategory_info_data = new_subcategory.dict()
    subcategory_info_data['category'] = subcategory_data.category  # use the retrieved category's title

    # Return the SubCategoryInfoSchema instance
    return SubCategoryCrateInfoSchema(**subcategory_info_data)
